import random
import argparse
from PIL import Image, ImageDraw

def createSpacingDepthExample():
    """创建间距深度示例图"""
    # 需要提前准备test/a.png, b.png, c.png文件
    tiles = [Image.open('test/a.png'), Image.open('test/b.png'),
             Image.open('test/c.png')]
    img = Image.new('RGB', (600, 400), (0, 0, 0))  # 创建黑色背景
    spacing = [10, 20, 40]  # 不同行的间距值
    # 平铺演示
    for j, tile in enumerate(tiles):
        for i in range(8):
            # 计算位置：横向增加偏移，纵向每行间隔100像素
            x = 10 + i * (100 + j * 10)
            y = 10 + j * 100
            img.paste(tile, (x, y))
    img.save('sdepth.png')

def createRandomTile(dims):
    """生成随机纹理瓷砖"""
    img = Image.new('RGB', dims)  # 创建新图像
    draw = ImageDraw.Draw(img)    # 创建绘图对象
    r = int(min(*dims)/100)       # 椭圆半径
    n = 1000                      # 椭圆数量
    # 随机绘制椭圆
    for _ in range(n):
        # 随机位置
        x = random.randint(0, dims[0]-r)
        y = random.randint(0, dims[1]-r)
        # 随机颜色
        fill = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        # 绘制椭圆
        draw.ellipse((x-r, y-r, x+r, y+r), fill=fill)
    return img

def createTiledImage(tile, dims):
    """创建平铺图像"""
    img = Image.new('RGB', dims)  # 目标图像
    W, H = dims                   # 目标尺寸
    w, h = tile.size              # 瓷砖尺寸
    # 计算行列数
    cols = int(W/w) + 1
    rows = int(H/h) + 1
    # 平铺操作
    for i in range(rows):
        for j in range(cols):
            img.paste(tile, (j*w, i*h))  # 按行列位置粘贴
    return img

def createDepthMap(dims):
    """创建示例深度图"""
    dmap = Image.new('L', dims)  # 创建灰度图
    # 绘制三个矩形区域
    dmap.paste(10, (200, 25, 300, 125))  # 浅灰区域(远)
    dmap.paste(30, (200, 150, 300, 250)) # 中灰区域(中)
    dmap.paste(20, (200, 275, 300, 375)) # 深灰区域(近)
    return dmap

def createDepthShiftedImage(dmap, img):
    """创建深度偏移图像"""
    assert dmap.size == img.size
    sImg = img.copy()  # 创建副本
    pixD = dmap.load() # 深度图像素访问对象
    pixS = sImg.load() # 结果图像像素访问对象
    cols, rows = sImg.size
    for j in range(rows):
        for i in range(cols):
            xshift = pixD[i, j]        # 从深度图获取偏移量
            xpos = i - 140 + xshift    # 计算新位置
            # 边界检查
            if 0 <= xpos < cols:
                # 应用像素偏移
                pixS[i, j] = pixS[xpos, j]
    return sImg

def createAutoStereogram(dmap, tile=None):
    """生成自动立体图核心函数"""
    # 确保深度图为灰度模式
    if dmap.mode != 'L':
        dmap = dmap.convert('L')
    # 生成或使用提供的瓷砖
    if not tile:
        tile = createRandomTile((100, 100))  # 默认生成100x100瓷砖
    # 创建平铺底图
    img = createTiledImage(tile, dmap.size)
    sImg = img.copy()  # 创建结果图像副本
    # 获取像素访问对象
    pixD = dmap.load()  # 深度图像素
    pixS = sImg.load()  # 立体图像素
    cols, rows = sImg.size
    # 根据深度图偏移像素
    for j in range(rows):
        for i in range(cols):
            # 计算偏移量
            xshift = pixD[i, j] // 10   # 缩小偏移量比例
            xpos = i - tile.size[0] + xshift  # 使用瓷砖宽度作为基准偏移
            # 边界检查
            if 0 <= xpos < cols:
                pixS[i, j] = pixS[xpos, j]
    return sImg

def main():
    """主函数"""
    print("正在生成自动立体图...")
    # 配置命令行参数
    parser = argparse.ArgumentParser(description="自动立体图生成器")
    parser.add_argument('--depth', dest='dmFile', required=True,
                       help='输入深度图文件路径')
    parser.add_argument('--tile', dest='tileFile', required=False,
                       help='可选瓷砖纹理文件路径')
    parser.add_argument('--out', dest='outFile', required=False,
                       help='输出文件路径(默认as.png)')
    args = parser.parse_args()
    # 处理输出路径
    outFile = 'as.png'
    if args.outFile:
        outFile = args.outFile
    # 加载瓷砖文件
    tile = None
    if args.tileFile:
        try:
            tile = Image.open(args.tileFile)
        except FileNotFoundError:
            print(f"错误：瓷砖文件 {args.tileFile} 不存在")
            return
    # 加载深度图
    try:
        dmImg = Image.open(args.dmFile)
    except FileNotFoundError:
        print(f"错误：深度图文件 {args.dmFile} 不存在")
        return
    # 生成并保存
    asImg = createAutoStereogram(dmImg, tile)
    asImg.save(outFile)
    print(f"已保存立体图至：{outFile}")

if __name__ == '__main__':
    main()