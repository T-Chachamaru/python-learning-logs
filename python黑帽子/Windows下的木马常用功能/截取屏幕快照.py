# 导入所需模块
import win32gui
import win32ui
import win32con
import win32api

def capture_screenshot(filename='screenshot.bmp'):
    """
    捕获整个虚拟屏幕的截图并保存为 BMP 文件
    参数:
        filename: 保存截图的文件名，默认为 'screenshot.bmp'
    """
    try:
        # 获取桌面窗口句柄
        hdesktop = win32gui.GetDesktopWindow()

        # 获取虚拟屏幕的尺寸和位置（支持多显示器）
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

        # 获取桌面窗口的设备上下文 (DC)
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        # 从桌面 DC 创建 PyCDC 对象
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)

        # 创建兼容的内存 DC，用于存储截图
        mem_dc = img_dc.CreateCompatibleDC()

        # 创建位图对象，用于保存截图
        screenshot = win32ui.CreateBitmap()
        # 初始化位图，指定宽度和高度
        screenshot.CreateCompatibleBitmap(img_dc, width, height)
        # 将位图对象选择到内存 DC 中
        mem_dc.SelectObject(screenshot)

        # 执行位图拷贝，将屏幕内容从 img_dc 复制到 mem_dc
        mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

        # 保存位图到指定文件
        screenshot.SaveBitmapFile(mem_dc, filename)

        # 清理资源
        mem_dc.DeleteDC()
        win32gui.DeleteObject(screenshot.GetHandle())
        img_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, desktop_dc)

        print(f"截图已保存为 {filename}")

    except Exception as e:
        print(f"截图失败: {e}")

        # 确保即使发生错误也清理资源
        try:
            mem_dc.DeleteDC()
        except:
            pass
        try:
            win32gui.DeleteObject(screenshot.GetHandle())
        except:
            pass
        try:
            img_dc.DeleteDC()
        except:
            pass
        try:
            win32gui.ReleaseDC(hdesktop, desktop_dc)
        except:
            pass

if __name__ == "__main__":
    capture_screenshot()