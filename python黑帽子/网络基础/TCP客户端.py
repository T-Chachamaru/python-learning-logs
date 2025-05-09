import socket

target_host = "127.0.0.1"
target_port = 9999

# 创建一个socket对象,使用默认的IPv4和TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 连接到服务器
client.connect((target_host, target_port))

# 向服务器发送一些数据(HTTP请求)
client.send(b"AAACCC")

# 接受服务器响应
response = client.recv(4096)

print(response)