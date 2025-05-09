import re
import zlib
import cv2
import os
from scapy.all import *

# 定义存储提取图片和人脸检测图片的目录
pictures_directory = "/home/justin/pic_carver/pictures"
faces_directory = "/home/justin/pic_carver/faces"
pcap_file = "bhp.pcap"

# 确保输出目录存在
def ensure_directory(directory):
    # 检查并创建目录（如果不存在）
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_http_headers(http_payload):
    # 从HTTP负载中提取头部信息
    try:
        # 使用双CRLF分隔头部和负载
        headers_raw, _ = http_payload.split(b"\r\n\r\n", 1)
        # 将原始头部解码为字符串以进行正则解析
        headers_raw = headers_raw.decode('utf-8', errors='ignore')
        # 使用正则表达式解析头部为字典
        headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", headers_raw))
    except:
        return None
    # 检查是否包含Content-Type头部
    if "Content-Type" not in headers:
        return None
    return headers

def extract_image(headers, http_payload):
    # 初始化图片数据和类型变量
    image = None
    image_type = None

    try:
        # 检查Content-Type是否表示图片
        if "image" in headers["Content-Type"]:
            # 从Content-Type中提取图片类型（例如jpeg、png）
            image_type = headers["Content-Type"].split("/")[1]
            # 提取头部-负载分隔符后的图片数据
            image = http_payload[http_payload.index(b"\r\n\r\n") + 4:]

            # 如果存在Content-Encoding，处理压缩图片
            try:
                if "Content-Encoding" in headers.keys():
                    if "gzip" in headers["Content-Encoding"]:
                        # 解压gzip编码的图片
                        image = zlib.decompress(image, 16 + zlib.MAX_WBITS)
                    elif "deflate" in headers["Content-Encoding"]:
                        # 解压deflate编码的图片
                        image = zlib.decompress(image)
            except zlib.error:
                # 记录解压错误并继续
                print("解压图片数据时出错，跳过处理")
                return None, None
    except:
        return None, None
    
    return image, image_type

def face_detect(path, image_name):
    # 从指定路径加载图片
    img = cv2.imread(path)
    if img is None:
        return False
    # 加载用于正面人脸检测的Haar级联分类器
    cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")
    if cascade.empty():
        print("无法加载Haar级联分类器文件")
        return False
    # 在图片中检测人脸
    rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=4, 
                                     flags=cv2.CASCADE_SCALE_IMAGE, minSize=(20, 20))

    # 如果未检测到人脸，返回False
    if len(rects) == 0:
        return False
    
    # 将矩形坐标转换为(x1, y1, x2, y2)格式
    rects[:, 2:] += rects[:, :2]

    # 在检测到的人脸上绘制矩形
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # 将带矩形的图片保存到人脸目录
    output_path = os.path.join(faces_directory, f"{pcap_file}-{image_name}")
    cv2.imwrite(output_path, img)

    return True

def http_assembler():
    # 初始化提取图片和检测人脸的计数器
    carved_images = 0
    faces_detected = 0

    # 确保输出目录存在
    ensure_directory(pictures_directory)
    ensure_directory(faces_directory)

    try:
        # 从pcap文件中读取数据包
        packets = rdpcap(pcap_file)
    except FileNotFoundError:
        print(f"无法找到pcap文件：{pcap_file}")
        return 0, 0

    # 按会话分组数据包
    sessions = packets.sessions()
    for session in sessions:
        # 初始化HTTP负载缓冲区
        http_payload = b""
        for packet in sessions[session]:
            try:
                # 检查数据包是否为HTTP（端口80）
                if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                    # 将TCP负载追加到缓冲区（保持为字节类型）
                    http_payload += bytes(packet[TCP].payload)
            except:
                continue
        
        # 从负载中提取头部
        headers = get_http_headers(http_payload)
        if headers is None:
            continue

        # 提取图片数据和类型
        image, image_type = extract_image(headers, http_payload)
        if image is None or image_type is None:
            continue

        # 生成唯一的图片文件名
        image_name = f"{pcap_file}-pic_carver_{carved_images}.{image_type}"
        image_path = os.path.join(pictures_directory, image_name)
        
        try:
            # 将提取的图片保存到图片目录
            with open(image_path, "wb") as fd:
                fd.write(image)
            carved_images += 1

            # 调整图片大小并保存到人脸目录
            result = cv2.imread(image_path)
            if result is not None:
                result = cv2.resize(result, (150, 150))
                cv2.imwrite(os.path.join(faces_directory, image_name), result)
                # 检测人脸
                if face_detect(image_path, image_name):
                    faces_detected += 1
        except IOError as e:
            print(f"保存图片 {image_name} 时出错：{e}")
            continue

    return carved_images, faces_detected

# 调用组装函数并打印结果
carved_images, faces_detected = http_assembler()
print(f"提取了 {carved_images} 张图片")
print(f"检测到 {faces_detected} 张人脸")