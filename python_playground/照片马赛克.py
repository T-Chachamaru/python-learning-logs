import os
import sys
import random
import argparse
from PIL import Image
import imghdr
import numpy as np
from scipy.spatial import KDTree


def getImages(imageDir):
    """
    从指定目录读取所有有效的图像文件并返回Image对象列表
    """
    files = os.listdir(imageDir)
    images = []
    for file in files:
        filePath = os.path.abspath(os.path.join(imageDir, file))
        try:
            with open(filePath, 'rb') as fp:
                im = Image.open(fp)
                im.load()  # 立即加载图像数据以便后续操作
                images.append(im)
        except Exception as e:
            print(f"无效图像文件：{filePath}，错误：{str(e)}")
    return images


def getAverageRGB(image):
    """
    计算图像的平均RGB值
    """
    im = np.array(image)  # 将图像转换为numpy数组
    w, h, d = im.shape
    return tuple(np.average(im.reshape(w*h, d), axis=0))  # 展平后计算均值


def splitImage(image, size):
    """
    将目标图像分割成指定网格大小的小块
    """
    W, H = image.size
    m, n = size
    w, h = int(W/n), int(H/m)
    imgs = []
    # 按行列循环切割图像
    for j in range(m):
        for i in range(n):
            # 计算每个小块的坐标区域
            box = (i*w, j*h, (i+1)*w, (j+1)*h)
            imgs.append(image.crop(box))
    return imgs


def getImageFilenames(imageDir):
    """
    获取目录下所有图像文件的路径
    """
    files = os.listdir(imageDir)
    filenames = []
    for file in files:
        filePath = os.path.abspath(os.path.join(imageDir, file))
        try:
            imgType = imghdr.what(filePath)  # 检测文件类型
            if imgType:
                filenames.append(filePath)
        except:
            print(f"无效文件：{filePath}")
    return filenames


def getBestMatchIndex(input_avg, avgs):
    """
    根据RGB平均值找到最佳匹配图像的索引
    """
    min_index = 0
    min_dist = float("inf")
    # 遍历所有平均值计算欧氏距离
    for i, val in enumerate(avgs):
        dist = sum(( (val[0] - input_avg[0])**2,
                     (val[1] - input_avg[1])**2,
                     (val[2] - input_avg[2])**2 ))
        if dist < min_dist:
            min_dist = dist
            min_index = i
    return min_index


def createImageGrid(images, dims):
    """
    将图像块排列成网格生成最终马赛克
    """
    m, n = dims
    assert m*n == len(images), "图像数量与网格尺寸不匹配"
    # 计算每个小图的尺寸（取最大尺寸）
    width = max(img.size[0] for img in images)
    height = max(img.size[1] for img in images)
    # 创建新画布
    grid_img = Image.new('RGB', (n*width, m*height))
    # 将每个小图粘贴到对应位置
    for index, img in enumerate(images):
        row = index // n  # 计算行号
        col = index % n   # 计算列号
        grid_img.paste(img, (col*width, row*height))
    return grid_img


def createPhotomosaic(target_image, input_images, grid_size, reuse_images=True):
    """
    创建马赛克主逻辑
    """
    print("正在分割目标图像...")
    target_images = splitImage(target_image, grid_size)
    print("正在计算素材图平均RGB...")
    avgs = [getAverageRGB(img) for img in input_images]
    # 创建素材副本以避免修改原始列表
    input_images_working = list(input_images)
    avgs_working = list(avgs)
    avgs_array = np.array(avgs_working)
    tree = KDTree(avgs_array) if avgs_working else None
    print("开始匹配最佳图像...")
    output_images = []
    count = 0
    total = len(target_images)
    batch_size = max(int(total/10), 1)
    for img in target_images:
        if not avgs_working:  # 无可用素材时提前终止
            break
        avg = getAverageRGB(img)
        avg_array = np.array(avg)
        # 使用K-D树查询最近邻
        distance, index = tree.query(avg_array)
        match_index = index
        output_images.append(input_images_working[match_index])
        if not reuse_images:
            # 删除已用素材并更新K-D树
            del input_images_working[match_index]
            del avgs_working[match_index]
            if avgs_working:
                avgs_array = np.array(avgs_working)
                tree = KDTree(avgs_array)
            else:
                tree = None
        # 更新进度
        if count % batch_size == 0 and count > 0:
            print(f"已完成 {count}/{total} ({count/total:.1%})...")
        count += 1
    print("正在合成马赛克...")
    return createImageGrid(output_images, grid_size)

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="生成照片马赛克")
    parser.add_argument('--target-image', required=True, help='目标图像路径')
    parser.add_argument('--input-folder', required=True, help='素材图片目录')
    parser.add_argument('--grid-size', nargs=2, type=int, required=True, 
                        metavar=('ROWS', 'COLS'), help='马赛克网格尺寸 如 128 128')
    parser.add_argument('--output-file', help='输出文件名,默认为mosaic.png')
    parser.add_argument('--reuse-images', action='store_true', 
                   help='允许重复使用素材图片')
    args = parser.parse_args()
    # 读取目标图像
    try:
        target_image = Image.open(args.target_image)
    except Exception as e:
        sys.exit(f"无法打开目标图像：{str(e)}")
    # 读取素材图像
    print("正在加载素材图片...")
    input_images = getImages(args.input_folder)
    if not input_images:
        sys.exit(f"错误：在 {args.input_folder} 中未找到有效图片")
    # 打乱素材顺序以获得随机效果
    random.shuffle(input_images)
    # 设置网格尺寸
    grid_size = (args.grid_size[0], args.grid_size[1])
    # 检查非重复模式下的素材数量是否足够
    if not args.reuse_images and (grid_size[0]*grid_size[1] > len(input_images)):
        sys.exit("错误：素材图片数量不足且不允许重复使用")
    # 调整素材图片尺寸
    print("正在调整素材尺寸...")
    # 计算每个小图的建议尺寸
    tile_width = target_image.width // grid_size[1]
    tile_height = target_image.height // grid_size[0]
    print(f"每个小图尺寸：{tile_width}x{tile_height}")
    # 使用缩略图保持比例
    for img in input_images:
        img.thumbnail((tile_width, tile_height))
    # 生成马赛克
    print("开始生成马赛克...")
    mosaic_image = createPhotomosaic(target_image, input_images, grid_size)
    # 保存结果
    output_filename = args.output_file or 'mosaic.png'
    mosaic_image.save(output_filename)
    print(f"马赛克已保存至 {output_filename}")

if __name__ == '__main__':
    main()