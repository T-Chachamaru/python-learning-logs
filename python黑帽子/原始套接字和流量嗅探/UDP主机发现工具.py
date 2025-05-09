import socket
import os
import struct
from ctypes import *
import threading
import time
from netaddr import IPNetwork, IPAddress

# 定义主机IP地址
host = "192.168.0.187"

# 定义子网范围，用于扫描
subnet = "192.168.0.0/24"

# 定义用于探测的魔法消息
magic_message = "PYTHONRULES!"

# UDP发送函数，向子网内所有IP发送探测消息
def udp_sender(subnet, magic_message):
    # 延迟5秒以确保嗅探器启动
    time.sleep(5)
    # 创建UDP套接字
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 遍历子网中的每个IP地址
    for ip in IPNetwork(subnet):
        try:
            # 向目标IP的65212端口发送魔法消息
            sender.sendto(magic_message.encode(), (str(ip), 65212))
        except Exception as e:
            # 忽略发送失败的错误
            pass
    # 关闭UDP套接字
    sender.close()

# 定义IP头部结构，使用ctypes创建C风格的结构体来解析IP头部
class IP(Structure):
    # 定义IP头部的字段及其类型、位宽
    _fields_ = [
        ("ihl", c_ubyte, 4),       # IP头部长度（4位）
        ("version", c_ubyte, 4),   # IP版本（4位）
        ("tos", c_ubyte),          # 服务类型
        ("len", c_ushort),         # 总长度
        ("id", c_ushort),          # 标识
        ("offset", c_ushort),      # 片偏移
        ("ttl", c_ubyte),          # 生存时间
        ("protocol_num", c_ubyte), # 协议号
        ("sum", c_ushort),         # 校验和
        ("src", c_ulong),          # 源IP地址
        ("dst", c_ulong)           # 目的IP地址
    ]

    # 重写__new__方法，用于从缓冲区创建IP结构体实例
    def __new__(self, socket_buffer=None):
        return self.from_buffer_copy(socket_buffer)
    
    # 初始化方法，解析IP地址和协议
    def __init__(self, socket_buffer=None):
        # 定义协议映射字典，将协议号映射为协议名称
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}

        # 将源IP和目的IP从整数转换为字符串格式（如"192.168.0.1"）
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))

        # 尝试将协议号转换为协议名称，若无匹配则直接使用协议号
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            self.protocol = str(self.protocol_num)

# 定义ICMP头部结构
class ICMP(Structure):
    # 定义ICMP头部的字段
    _fields_ = [
        ("type", c_ubyte),      # 类型
        ("code", c_ubyte),      # 代码
        ("checksum", c_ushort), # 校验和
        ("unused", c_ushort),   # 未使用
        ("next_hop", c_ushort)  # 下一跳
    ]

    # 重写__new__方法，用于从缓冲区创建ICMP结构体实例
    def __new__(self, socket_buffer):
        return self.from_buffer_copy(socket_buffer)
    
    # 初始化方法
    def __init__(self, socket_buffer=None):
        pass

# 根据操作系统选择协议类型
# Windows使用IPPROTO_IP，Linux使用IPPROTO_ICMP
if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP
else:
    socket_protocol = socket.IPPROTO_ICMP

# 创建原始套接字
# AF_INET表示IPv4，SOCK_RAW表示原始套接字，socket_protocol指定协议
sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)

# 将套接字绑定到指定主机和端口（0表示任意端口）
sniffer.bind((host, 0))

# 设置IP头部包含选项，确保接收的数据包包含IP头部
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# 如果是Windows系统，启用混杂模式以捕获所有网络流量
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

# 启动UDP发送线程，向子网内广播魔法消息
t = threading.Thread(target=udp_sender, args=(subnet, magic_message))
t.start()

try:
    # 循环接收数据包
    while True:
        # 接收数据包，缓冲区大小为65565字节，获取数据部分
        raw_buffer = sniffer.recvfrom(65565)[0]
        # 解析前20字节（IP头部），创建IP结构体实例
        ip_header = IP(raw_buffer[0:20])
        # 打印协议类型、源IP地址和目的IP地址
        print("协议: %s %s -> %s" % (ip_header.protocol, ip_header.src_address, ip_header.dst_address))

        # 如果是ICMP协议，进一步解析
        if ip_header.protocol == "ICMP":
            # 计算ICMP头部偏移量（IP头部长度 * 4字节）
            offset = ip_header.ihl * 4
            # 提取ICMP头部数据
            buf = raw_buffer[offset:offset + sizeof(ICMP)]
            # 创建ICMP结构体实例
            icmp_header = ICMP(buf)
            # 打印ICMP类型和代码
            print("ICMP -> 类型: %d 代码: %d" % (icmp_header.type, icmp_header.code))

            # 检查ICMP类型和代码是否为3（目的不可达）
            if icmp_header.code == 3 and icmp_header.type == 3:
                # 验证源IP是否在指定子网内
                if IPAddress(ip_header.src_address) in IPNetwork(subnet):
                    # 检查数据包末尾是否包含魔法消息（需解码为字符串）
                    if raw_buffer[len(raw_buffer) - len(magic_message):].decode() == magic_message:
                        # 打印活跃主机
                        print("主机活跃: %s" % ip_header.src_address)

# 捕获键盘中断（Ctrl+C），优雅退出
except KeyboardInterrupt:
    # 如果是Windows系统，关闭混杂模式
    if os.name == "nt":
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
finally:
    # 关闭嗅探器套接字，释放资源
    sniffer.close()