import sys
import socket
import threading
import binascii

# 服务器循环函数，监听本地端口并转发数据到远程主机
def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    """
    创建 TCP 服务器，监听本地主机和端口，将数据转发到远程主机。
    参数:
        local_host (str): 本地主机地址（如 "127.0.0.1"）。
        local_port (int): 本地监听端口。
        remote_host (str): 远程主机地址。
        remote_port (int): 远程主机端口。
        receive_first (bool): 是否先从远程主机接收数据。
    """
    # 创建 TCP 套接字
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # 绑定本地主机和端口
        server.bind((local_host, local_port))
    except Exception as e:
        print(f"[!!] 无法监听 {local_host}:{local_port}：{e}")
        print("[!!] 请检查是否有其他程序占用端口或权限问题")
        sys.exit(0)
    
    # 打印监听信息
    print(f"[*] 监听 {local_host}:{local_port}")

    # 设置最大连接队列长度为 5
    server.listen(5)

    # 持续接受客户端连接
    while True:
        client_socket, addr = server.accept()
        print(f"[==>] 接收到来自 {addr[0]}:{addr[1]} 的连接")
        # 为每个客户端连接创建线程，调用代理处理函数
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first)
        )
        proxy_thread.start()

# 主函数，解析命令行参数并启动服务器
def main():
    """
    解析命令行参数并调用服务器循环函数。
    """
    # 检查参数数量是否正确
    if len(sys.argv[1:]) != 5:
        print("用法: python tcp_proxy.py [本地主机] [本地端口] [远程主机] [远程端口] [是否先接收]")
        print("示例: python tcp_proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    
    # 提取参数
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])
    receive_first = sys.argv[5]

    # 将 receive_first 转换为布尔值
    receive_first = receive_first.lower() == "true"
    
    # 调用服务器循环
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

# 代理处理函数，处理客户端和远程主机之间的数据转发
def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    """
    在客户端和远程主机之间转发数据，支持数据修改。
    参数:
        client_socket (socket): 客户端套接字。
        remote_host (str): 远程主机地址。
        remote_port (int): 远程主机端口。
        receive_first (bool): 是否先从远程主机接收数据。
    """
    # 创建远程主机套接字并连接
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # 如果需要先从远程主机接收数据
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        # 处理远程主机的响应
        remote_buffer = response_handler(remote_buffer)

        # 如果有数据，发送到客户端
        if len(remote_buffer):
            print(f"[<==] 发送 {len(remote_buffer)} 字节到本地主机")
            client_socket.send(remote_buffer)
    
    # 主循环：双向转发数据
    while True:
        # 从客户端接收数据
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print(f"[==>] 从本地主机接收到 {len(local_buffer)} 字节")
            hexdump(local_buffer)

            # 处理客户端请求
            local_buffer = request_handler(local_buffer)

            # 发送到远程主机
            remote_socket.send(local_buffer)
            print("[==>] 已发送到远程主机")
        
        # 从远程主机接收数据
        remote_buffer = receive_from(remote_socket)

        if len(remote_buffer):
            print(f"[<==] 从远程主机接收到 {len(remote_buffer)} 字节")
            hexdump(remote_buffer)

            # 处理远程主机响应
            remote_buffer = response_handler(remote_buffer)

            # 发送到客户端
            client_socket.send(remote_buffer)
            print("[<==] 已发送到本地主机")

        # 如果任一方无数据，关闭连接
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] 无更多数据，关闭连接")
            break

# 十六进制转储函数，显示数据的十六进制和 ASCII 表示
def hexdump(src, length=16):
    """
    将字节数据以十六进制和 ASCII 格式打印。
    参数:
        src (bytes): 要转储的字节数据。
        length (int): 每行显示的字节数，默认为 16。
    """
    result = []
    for i in range(0, len(src), length):
        s = src[i:i + length]
        # 转换为十六进制
        hexa = ' '.join([f"{b:02X}" for b in s])
        # 转换为可打印 ASCII 字符，非可打印字符显示为点
        text = ''.join([chr(b) if 0x20 <= b < 0x7F else '.' for b in s])
        result.append(f"{i:04X}   {hexa:<{length * 3}}   {text}")
    
    print('\n'.join(result))

# 从连接接收数据的函数
def receive_from(connection):
    """
    从套接字接收数据，直到无数据或超时。
    参数:
        connection (socket): 套接字对象。
    返回:
        bytes: 接收到的字节数据。
    """
    buffer = b""  # 使用字节类型
    connection.settimeout(2)  # 设置 2 秒超时
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except socket.timeout:
        pass  # 超时后返回已接收的数据
    except Exception as e:
        print(f"[!!] 接收数据失败：{e}")
    return buffer

# 处理客户端请求的函数（可扩展）
def request_handler(buffer):
    """
    处理从客户端接收到的数据，可进行数据修改。
    参数:
        buffer (bytes): 客户端数据。
    返回:
        bytes: 修改后的数据。
    """
    # 目前直接返回未修改的数据
    return buffer

# 处理远程主机响应的函数（可扩展）
def response_handler(buffer):
    """
    处理从远程主机接收到的数据，可进行数据修改。
    参数:
        buffer (bytes): 远程主机数据。
    返回:
        bytes: 修改后的数据。
    """
    # 目前直接返回未修改的数据
    return buffer

if __name__ == "__main__":
    main()