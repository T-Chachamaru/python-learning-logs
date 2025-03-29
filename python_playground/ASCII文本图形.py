import argparse
import numpy as np
from PIL import Image

# 定义两种灰度字符梯度，用于不同细节级别
gscale1 = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
gscale2 = '@%#*+=-:. '

def getAverageL(image):
    """计算图像块的平均亮度值"""
    im = np.array(image)          # 将PIL图像转换为numpy数组
    h, w = im.shape               # 获取图像尺寸（高度, 宽度）
    return np.average(im.reshape(h * w))  # 计算所有像素的平均亮度

def convertImageToAscii(fileName, cols, scale, moreLevels):
    """将图像转换为ASCII字符画"""
    global gscale1, gscale2
    # 打开图像并转换为灰度图
    image = Image.open(fileName).convert('L')  
    W, H = image.size  # 获取原始图像尺寸（宽度, 高度）
    print("输入图像尺寸: %d x %d" % (W, H))
    # 计算每个字符块的尺寸
    w = W / cols        # 单个字符块的宽度
    h = w / scale       # 根据宽高比计算字符块高度
    rows = int(H / h)   # 计算总行数
    print("列数: %d, 行数: %d" % (cols, rows))
    print("字符块尺寸: %.2f x %.2f" % (w, h))
    # 有效性检查
    if cols > W or rows > H:
        print("图像尺寸太小，无法分割为指定列数！")
        exit(0)
    aimg = []
    for j in range(rows):
        y1 = int(j * h)
        y2 = int((j + 1) * h)
        if j == rows - 1:  # 最后一行处理剩余像素
            y2 = H
        aimg.append("")
        for i in range(cols):
            x1 = int(i * w)
            x2 = int((i + 1) * w)
            if i == cols - 1:  # 最后一列处理剩余像素
                x2 = W
            # 截取当前字符块
            img = image.crop((x1, y1, x2, y2))
            # 计算平均亮度并映射到字符
            avg = int(getAverageL(img))
            gsval = gscale1[int((avg * 69) / 255)] if moreLevels else gscale2[int((avg * 9) / 255)]
            aimg[j] += gsval
    return aimg

def main():
    # 命令行参数解析
    descStr = "本程序将图像转换为ASCII字符画"
    parser = argparse.ArgumentParser(description=descStr)
    parser.add_argument('--file', dest='imgFile', required=True, help='输入图像文件路径')
    parser.add_argument('--scale', dest='scale', required=False, help='宽高比例因子(默认0.43)')
    parser.add_argument('--out', dest='outFile', required=False, help='输出文件名(默认out.txt)')
    parser.add_argument('--cols', dest='cols', required=False, help='输出列数(默认80)')
    parser.add_argument('--morelevels', dest='moreLevels', action='store_true', help='使用70级灰度字符(默认10级)')
    args = parser.parse_args()
    # 参数处理
    outFile = 'out.txt' if not args.outFile else args.outFile
    scale = 0.43 if not args.scale else float(args.scale)
    cols = 80 if not args.cols else int(args.cols)
    print('正在生成ASCII艺术...')
    aimg = convertImageToAscii(args.imgFile, cols, scale, args.moreLevels)
    # 写入输出文件
    with open(outFile, 'w') as f:
        for row in aimg:
            f.write(row + '\n')
    print('ASCII艺术已保存至 %s' % outFile)

if __name__ == '__main__':
    main()