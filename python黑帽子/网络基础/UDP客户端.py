import socket

target_host = "127.0.0.1"
target_port = 80

# 创建一个socket对象,使用IPV4和UDP
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 发送数据,到目标服务器,不需要connect建立连接
client.sendto(b"AAABBBCCC", (target_host, target_port))

# 接受服务器的响应
data, addr = client.recvfrom(4096)

print(data)