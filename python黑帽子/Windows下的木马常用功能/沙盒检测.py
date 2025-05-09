import ctypes
import random
import time
import sys

# 初始化 Windows API 动态链接库
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 全局计数器
keystrokes = 0  # 键盘按键次数
mouse_clicks = 0  # 鼠标点击次数
double_clicks = 0  # 鼠标双击次数

# 定义 LASTINPUTINFO 结构体，用于获取最后输入事件的时间
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint),  # 结构体大小
        ('dwTime', ctypes.c_ulong)  # 最后输入事件的时间（以毫秒为单位）
    ]

def get_last_input():
    """
    获取自系统启动以来最后一次用户输入（键盘或鼠标）经过的时间
    返回:
        elapsed: 自最后输入以来的毫秒数
    """
    try:
        # 初始化 LASTINPUTINFO 结构体
        struct_lastinputinfo = LASTINPUTINFO()
        struct_lastinputinfo.cbSize = ctypes.sizeof(LASTINPUTINFO)  # 设置结构体大小

        # 调用 GetLastInputInfo 获取最后输入时间
        if not user32.GetLastInputInfo(ctypes.byref(struct_lastinputinfo)):
            raise ctypes.WinError()  # 如果调用失败，抛出 Windows 错误

        # 获取系统运行时间（以毫秒为单位）
        run_time = kernel32.GetTickCount()

        # 计算自最后输入以来的时间
        elapsed = run_time - struct_lastinputinfo.dwTime

        print(f"[*] 距离最后输入事件已过去 {elapsed} 毫秒。")

        return elapsed

    except Exception as e:
        print(f"[错误] 获取最后输入时间失败: {e}")
        return 0

def get_key_press():
    """
    检测键盘和鼠标输入事件，更新全局计数器
    返回:
        当前时间戳（如果检测到输入事件），否则返回 None
    """
    global mouse_clicks, keystrokes

    try:
        # 遍历所有可能的虚拟键码 (0x00 到 0xFF)
        for i in range(0xFF):
            # 检查异步按键状态，-32767 表示按键被按下
            if user32.GetAsyncKeyState(i) & 0x8000:  # 使用位运算检查高位
                # 鼠标左键 (0x01)
                if i == 0x01:
                    mouse_clicks += 1
                    return time.time()
                # 可打印字符 (ASCII 33-255)
                elif 32 < i < 256:
                    keystrokes += 1

        return None

    except Exception as e:
        print(f"[错误] 检测按键失败: {e}")
        return None

def detect_sandbox():
    """
    通过监控用户输入行为检测是否运行在沙箱环境中
    如果检测到异常行为（例如长时间无输入或输入模式不符合人类行为），退出程序
    """
    global mouse_clicks, keystrokes, double_clicks

    try:
        # 设置随机阈值，模拟人类输入的多样性
        max_keystrokes = random.randint(10, 25)  # 最大按键次数
        max_mouse_clicks = random.randint(5, 25)  # 最大鼠标点击次数
        max_double_clicks = 10  # 最大双击次数
        double_click_threshold = 0.250  # 双击时间阈值（秒）
        max_input_threshold = 30000  # 最大无输入时间（毫秒）

        first_double_click = None  # 第一次双击的时间
        previous_timestamp = None  # 上一次输入的时间戳

        # 检查最后输入时间是否过长（沙箱可能无用户交互）
        last_input = get_last_input()
        if last_input >= max_input_threshold:
            print("[*] 检测到长时间无输入，可能是沙箱环境，退出！")
            sys.exit(0)

        # 主循环，检测用户输入
        while True:
            keypress_time = get_key_press()

            if keypress_time is not None and previous_timestamp is not None:
                # 计算两次输入之间的时间间隔
                elapsed = keypress_time - previous_timestamp

                # 检测双击（时间间隔小于阈值）
                if elapsed <= double_click_threshold:
                    double_clicks += 1
                    if first_double_click is None:
                        first_double_click = keypress_time
                    else:
                        # 如果双击次数达到阈值且时间过短，认为是沙箱
                        if double_clicks >= max_double_clicks:
                            if keypress_time - first_double_click <= (max_double_clicks * double_click_threshold):
                                print("[*] 检测到异常双击模式，可能是沙箱环境，退出！")
                                sys.exit(0)

                # 如果输入行为达到阈值，认为是正常用户环境
                if (keystrokes >= max_keystrokes and
                    mouse_clicks >= max_mouse_clicks and
                    double_clicks >= max_double_clicks):
                    print("[*] 输入行为正常，确认非沙箱环境！")
                    return

                previous_timestamp = keypress_time

            elif keypress_time is not None:
                previous_timestamp = keypress_time

            # 短暂休眠，降低 CPU 使用率
            time.sleep(0.01)

    except Exception as e:
        print(f"[错误] 沙箱检测失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 运行沙箱检测
    detect_sandbox()
    print("我们没事！")