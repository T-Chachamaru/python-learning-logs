import win32api
import win32security
import wmi
import logging
import sys
import datetime

# 配置日志
LOG_FILE = "process_monitor.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_process_privileges(pid):
    """
    获取指定进程的特权信息
    参数:
        pid: 进程 ID
    返回:
        特权名称列表（以 '|' 分隔），或 "N/A" 如果失败
    """
    try:
        # 打开进程句柄
        hproc = win32api.OpenProcess(win32api.PROCESS_QUERY_INFORMATION, False, pid)
        
        # 打开进程令牌
        htok = win32security.OpenProcessToken(hproc, win32security.TOKEN_QUERY)
        
        # 获取令牌特权信息
        privs = win32security.GetTokenInformation(htok, win32security.TokenPrivileges)
        
        # 提取启用和启用的特权（状态为 3）
        priv_list = []
        for priv_id, flags in privs:
            if flags == 3:  # SE_PRIVILEGE_ENABLED | SE_PRIVILEGE_ENABLED_BY_DEFAULT
                priv_list.append(win32security.LookupPrivilegeName(None, priv_id))
        
        return "|".join(priv_list) or "None"
    
    except Exception as e:
        logging.error(f"获取 PID {pid} 的特权失败: {e}")
        return "N/A"

def log_to_file(message):
    """
    将消息记录到日志文件
    参数:
        message: 要记录的消息（字符串或字节串）
    """
    try:
        with open(LOG_FILE, "a", encoding='utf-8') as fd:
            fd.write(f"{message}\r\n")
    except Exception as e:
        logging.error(f"写入日志失败: {e}")
        print(f"[错误] 写入日志失败: {e}")

def main():
    """
    主函数，监控新进程创建并记录详细信息
    """
    try:
        # 初始化日志文件（写入表头）
        log_to_file("Time,User,Executable,CommandLine,PID,Parent PID,Privileges")
        logging.info("进程监控启动")
        
        # 初始化 WMI 监控
        c = wmi.WMI()
        process_watcher = c.Win32_Process.watch_for("creation")
        
        print("开始监控新进程创建...")
        
        while True:
            try:
                # 等待新进程创建事件
                new_process = process_watcher()
                
                # 获取进程信息
                proc_owner = new_process.GetOwner()
                proc_owner = f"{proc_owner[0]}\\{proc_owner[2]}" if proc_owner[2] else "Unknown"
                create_date = new_process.CreationDate or "N/A"
                executable = new_process.ExecutablePath or "N/A"
                cmdline = new_process.CommandLine or "N/A"
                pid = new_process.ProcessId or 0
                parent_pid = new_process.ParentProcessId or 0
                privileges = get_process_privileges(pid)
                
                # 格式化日志消息
                process_log_message = f"{create_date},{proc_owner},{executable},{cmdline},{pid},{parent_pid},{privileges}"
                
                # 打印并记录日志
                print(process_log_message)
                log_to_file(process_log_message)
                logging.info(f"记录新进程: PID {pid}")
            
            except Exception as e:
                logging.error(f"处理新进程失败: {e}")
                print(f"[错误] 处理新进程失败: {e}")
    
    except KeyboardInterrupt:
        print("\n进程监控停止")
        logging.info("进程监控停止")
    except Exception as e:
        logging.error(f"主程序错误: {e}")
        print(f"[错误] 主程序错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()