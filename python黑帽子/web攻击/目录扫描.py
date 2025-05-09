import threading
import queue
import requests
import argparse
import logging
import urllib.parse

# 配置日志，记录爆破过程中的信息和错误
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 默认线程数
THREADS = 50

# 用户代理，伪装为浏览器请求
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"

# 文件扩展名列表
EXTENSIONS = [".php", ".bak", ".orig", ".inc"]

def build_wordlist(wordlist_file, resume=None):
    """
    构建词典队列，从文件中读取路径并存入队列
    :param wordlist_file: 词典文件路径
    :param resume: 恢复爆破的起始词（可选）
    :return: 包含路径的队列
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

def dir_brute(word_queue, target_url, extensions=None):
    """
    执行目录爆破，尝试访问目标 URL 的路径
    :param word_queue: 路径词典队列
    :param target_url: 目标网站 URL
    :param extensions: 文件扩展名列表
    """
    while not word_queue.empty():
        attempt = word_queue.get()
        attempt_list = []

        # 构建尝试路径
        if "." in attempt:
            attempt_list.append(f"/{attempt}")  # 已包含扩展名的路径
        else:
            attempt_list.append(f"/{attempt}/")  # 目录路径
            if extensions:
                for ext in extensions:
                    attempt_list.append(f"/{attempt}{ext}")  # 添加扩展名

        for brute in attempt_list:
            url = f"{target_url}{urllib.parse.quote(brute)}"
            try:
                headers = {"User-Agent": USER_AGENT}
                response = requests.get(url, headers=headers, timeout=5)
                
                # 检查响应状态码和内容
                if response.status_code != 404 and len(response.content) > 0:
                    logging.info("[%d] => %s", response.status_code, url)
            except requests.RequestException as e:
                logging.warning("访问 %s 失败: %s", url, str(e))
                continue

def main():
    """
    主函数，解析命令行参数并启动爆破
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="目录爆破工具")
    parser.add_argument("-u", "--url", required=True, help="目标网站 URL (如 http://example.com)")
    parser.add_argument("-w", "--wordlist", required=True, help="词典文件路径")
    parser.add_argument("-t", "--threads", type=int, default=THREADS, help="线程数")
    parser.add_argument("-r", "--resume", help="从指定词恢复爆破")
    args = parser.parse_args()

    # 验证目标 URL
    if not args.url.startswith("http"):
        args.url = f"http://{args.url}"
    logging.info("目标 URL: %s", args.url)

    # 构建词典队列
    word_queue = build_wordlist(args.wordlist, args.resume)
    logging.info("词典加载完成，词数: %d", word_queue.qsize())

    # 启动线程
    threads = []
    for i in range(args.threads):
        t = threading.Thread(target=dir_brute, args=(word_queue, args.url, EXTENSIONS))
        t.start()
        threads.append(t)

    # 等待所有线程完成
    for t in threads:
        t.join()

    logging.info("爆破完成")

if __name__ == "__main__":
    main()