import socket
import threading

# 允许所有的IP地址连接到9999端口
bind_ip = "0.0.0.0"
bind_port = 9999

# 创建一个TCP的socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定IP和端口，并开始监听
server.bind((bind_ip, bind_port))

# 将最大连接数设置为5
server.listen(5)

print("[*] Listening on %s:%d" % (bind_ip, bind_port))

# 定义一个处理客户端请求的函数
def handle_client(client_socket):

    # 接收客户端请求
    request = client_socket.recv(1021)

    print("[*] Received: %s" % request)

    # 返回服务器响应
    client_socket.send(b"ACK!")

    # 关闭连接
    client_socket.close()

while True:

    # 接受一个客户端连接,并把连接对象保存在client和addr变量中
    client, addr = server.accept()

    print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))

    # 为回调函数handle_client创建一个线程,并将client对象作为参数传递给它
    client_handler = threading.Thread(target=handle_client, args=(client,))

    # 启动线程开始处理客户端连接
    client_handler.start()