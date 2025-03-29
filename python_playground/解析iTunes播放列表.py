import argparse
from matplotlib import pyplot
import plistlib
import numpy as np

def findDuplicates(fileName):
    '''查找重复的曲目'''
    print('在 %s 中查找重复曲目...' % fileName)
    try:
        # 读取iTunes播放列表文件
        plist = plistlib.readPlist(fileName)
        tracks = plist['Tracks']
        trackNames = {}  # 存储曲目名称和出现次数
        # 遍历所有曲目
        for trackId, track in tracks.items():
            try:
                name = track['Name']
                duration = track['Total Time']  # 单位：毫秒
                # 检查是否存在同名曲目
                if name in trackNames:
                    # 检查时长是否相同（精确到秒）
                    if duration//1000 == trackNames[name][0]//1000:
                        count = trackNames[name][1]
                        trackNames[name] = (duration, count+1)
                else:
                    trackNames[name] = (duration, 1)
            except KeyError:
                pass
        # 收集重复曲目
        dups = []
        for name, (duration, count) in trackNames.items():
            if count > 1:
                dups.append((count, name))
        # 输出结果
        if dups:
            print("找到 %d 个重复曲目。已保存到 dup.txt" % len(dups))
            with open('dups.txt', 'w', encoding='utf-8') as f:
                for count, name in dups:
                    f.write("[%d] %s\n" % (count, name))
        else:
            print("未找到重复曲目！")
    except Exception as e:
        print("处理文件时出错：", str(e))

def findCommonTracks(fileNames):
    '''查找多个播放列表中共同的音轨'''
    trackNameSets = []
    for filename in fileNames:
        try:
            # 读取每个播放列表文件
            plist = plistlib.readPlist(filename)
            tracks = plist['Tracks']
            currentTracks = set()
            # 收集当前文件的曲目信息
            for trackId, track in tracks.items():
                try:
                    name = track['Name']
                    duration = track['Total Time']
                    currentTracks.add((name, duration))
                except KeyError:
                    pass
            trackNameSets.append(currentTracks)
        except Exception as e:
            print(f"读取文件 {filename} 时出错：{str(e)}")
            continue
    # 计算多个播放列表的交集
    commonTracks = set.intersection(*trackNameSets)
    if commonTracks:
        print("找到 %d 个共同曲目。已保存到 common.txt" % len(commonTracks))
        with open("common.txt", 'w', encoding='utf-8') as f:
            for name, duration in commonTracks:
                f.write(f"{name} ({duration//1000}秒)\n")
    else:
        print("没有共同曲目！")

def plotStats(fileName):
    '''收集并绘制统计信息'''
    try:
        plist = plistlib.readPlist(fileName)
        tracks = plist['Tracks']
        ratings = []
        durations = []
        # 收集评分和时长数据
        for trackId, track in tracks.items():
            try:
                ratings.append(track['Album Rating'])
                durations.append(track['Total Time'])
            except KeyError:
                pass  # 跳过缺少数据的曲目
        if not ratings or not durations:
            print("文件 %s 中缺少有效的评分或时长数据。" % fileName)
            return
        # 转换数据格式
        x = np.array(durations, np.int32) / 60000.0  # 转换为分钟
        y = np.array(ratings, np.int32)
        # 创建图表
        pyplot.figure(figsize=(10, 6))
        # 散点图：评分 vs 时长
        pyplot.subplot(2, 1, 1)
        pyplot.plot(x, y, 'o', alpha=0.5)
        pyplot.title('曲目评分与时长关系')
        pyplot.xlabel('时长（分钟）')
        pyplot.ylabel('评分')
        pyplot.grid(True)
        # 时长分布直方图
        pyplot.subplot(2, 1, 2)
        pyplot.hist(x, bins=20, edgecolor='black')
        pyplot.xlabel('时长（分钟）')
        pyplot.ylabel('数量')
        pyplot.title('曲目时长分布')
        pyplot.tight_layout()
        pyplot.show()
    except Exception as e:
        print("绘制统计数据时出错：", str(e))

def main():
    # 命令行参数配置
    descStr = """
    iTunes播放列表分析工具(支持.xml格式)
    功能包括：
      --common  查找多个播放列表的共同曲目
      --stats   生成单个播放列表的统计图表
      --dup     查找重复曲目
    """
    parser = argparse.ArgumentParser(description=descStr,
                                     formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    # 添加互斥参数
    group.add_argument('--common', nargs='+', metavar='FILE', 
                      help='查找多个播放列表的共同曲目', dest='plFiles')
    group.add_argument('--stats', metavar='FILE',
                      help='生成统计图表', dest='plFile')
    group.add_argument('--dup', metavar='FILE',
                      help='查找重复曲目', dest='plFileD')
    args = parser.parse_args()
    # 执行对应功能
    if args.plFiles:
        findCommonTracks(args.plFiles)
    elif args.plFile:
        plotStats(args.plFile)
    elif args.plFileD:
        findDuplicates(args.plFileD)
    else:
        # 没有参数时显示帮助信息
        parser.print_help()

if __name__ == '__main__':
    main()