import sys, os
import time, random
import wave, argparse, pygame
import numpy as np
from collections import deque
from matplotlib import pyplot as plt

# 全局控制是否显示波形图
gShowPlot = False
# 音符频率字典
pmNotes = { 'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494, 'C5': 523,
    'Eb4': 311, 'Bb4': 466}

def writeWAVE(fname, data):
    """将音频数据写入WAV文件"""
    with wave.open(fname, 'wb') as file:
        # 设置WAV文件参数
        nChannels = 1        # 单声道
        sampleWidth = 2      # 16位样本
        frameRate = 44100    # 采样率
        nFrames = len(data) // (sampleWidth * nChannels)      # 样本总数
        file.setparams((nChannels, sampleWidth, frameRate, nFrames, 
                       'NONE', 'noncompressed'))
        file.writeframes(data)

def generateNoteFloat(freq, duration=1.0):
    """使用Karplus-Strong算法生成音符波形数据"""
    num_samples = int(44100 * duration)      # 总样本数
    sample_rate = 44100      # 采样率
    N = max(1, int(sample_rate / freq))  # 计算周期长度
    # 初始化随机缓冲区（环形队列）
    buf = deque([random.random() - 0.5 for _ in range(N)])
    # 实时绘图设置
    if gShowPlot:
        plt.ion()           # 启用交互模式
        fig, ax = plt.subplots()
        axline, = ax.plot(buf)
    # 创建样本数组
    samples = np.zeros(num_samples, dtype=np.float32)
    
    for i in range(num_samples):
        samples[i] = buf[0]  # 取当前样本值
        # 计算相邻样本平均值并应用衰减
        avg = 0.995 * 0.5 * (buf[0] + buf[1])
        buf.append(avg)      # 将新值加入队列末尾
        buf.popleft()        # 移除队列首元素
        # 实时更新波形图
        if gShowPlot and i % 1000 == 0:
            axline.set_ydata(buf)
            ax.set_ylim(-1, 1)    # 固定Y轴范围
            fig.canvas.flush_events()  # 更新绘图
    return samples
    # 将浮点数组转换为16位整型（WAV格式要求）
    # samples = np.int16(samples * 32767)
    # return samples.tobytes()

def generateNote(freq):
    """生成16位整型的音符数据"""
    samplesFloat = generateNoteFloat(freq)
    samplesInt16 = (samplesFloat * 32767).astype(np.int16)
    return samplesInt16.tobytes()

def generateChord(freq1, freq2, delay=0.1, duration=2.0):
    """生成双音和弦(有延时)"""
    # 生成两个浮点波形
    samples1 = generateNoteFloat(freq1, duration)
    samples2 = generateNoteFloat(freq2, duration)
    # 计算延时样本数
    delaySamples = int(delay * 44100)
    totalSamples = max(len(samples1), len(samples2) + delaySamples)
    # 创建混合容器
    mixed = np.zeros(totalSamples, dtype=np.float32)
    # 叠加第一个音
    mixed[:len(samples1)] += samples1
    # 叠加带延时的第二个音
    start = min(delaySamples, totalSamples)
    end = min(delaySamples + len(samples2), totalSamples)
    mixed[start:end] += samples2[:end-start]
    # 限制幅值范围
    np.clip(mixed, -1.0, 1.0, out=mixed)
    # 转换为16位音频
    return (mixed * 32767).astype(np.int16).tobytes()

class NotePlayer:
    """音符播放器类(使用pygame.mixer)"""
    def __init__(self):
        # 初始化音频系统
        pygame.mixer.pre_init(44100, -16, 1, 2048)
        pygame.init()
        self.notes = {}      # 存储加载的音效
    
    def add(self, filename):
        """加载音符文件到内存"""
        self.notes[filename] = pygame.mixer.Sound(filename)
    
    def play(self, filename):
        """播放指定音符文件"""
        try:
            self.notes[filename].play()
        except KeyError:
            print(f"错误：未找到音频文件 {filename}")
    
    def playRandom(self):
        """随机播放一个音符"""
        if self.notes:
            random.choice(list(self.notes.values())).play()
    
    def playSequence(self, sequence, bpm=120):
        """按顺序播放音符序列"""
        for note, duration in sequence:
            if note == 'REST':
                time.sleep(duration * 60 / bpm)
            else:
                filename = f"{note}.wav"
                self.play(filename)
                time.sleep(duration * 60 /bpm) # 按节拍等待
    
def parseMusicFile(filename):
    """解析乐谱文件"""
    sequence = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) % 2 != 0:
                        raise ValueError("无效的乐谱格式")
                    for i in range(0, len(parts), 2):
                        note = parts[i]
                        duration = float(parts[i+1])
                        sequence.append((note, duration))
        return sequence
    except Exception as e:
        print(f"解析乐谱错误:{str(e)}")
        return None

def main():
    global gShowPlot
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="基于Karplus-Strong算法的电子琴")
    parser.add_argument('--display', action='store_true', 
                       help="显示波形生成过程")
    parser.add_argument('--play', action='store_true',
                       help="随机播放音符模式")
    parser.add_argument('--piano', action='store_true',
                       help="钢琴模式(使用A/S/D/F/G键演奏)")
    parser.add_argument('--chord', action='store_true', help="生成双音和弦示例")
    parser.add_argument('--playfile', type=str, help="播放乐谱文件")
    args = parser.parse_args()

    if args.display:
        gShowPlot = True     # 启用实时波形显示
        plt.ion()            # 初始化Matplotlib交互模式
    
    nplayer = NotePlayer()   # 创建播放器实例

    # 生成/加载所有音符文件
    for name, freq in pmNotes.items():
        filename = f"{name}.wav"
        # 如果文件不存在或指定显示模式，则重新生成
        if not os.path.exists(filename) or args.display:
            print(f"生成音频文件: {filename}...")
            data = generateNote(freq)
            writeWAVE(filename, data)
        else:
            print(f"使用现有文件: {filename}")
        
        nplayer.add(filename)  # 将文件加载到播放器

        # 显示模式时试听每个音符
        if args.display:
            nplayer.play(filename)
            time.sleep(0.5)
    
    # 随机播放模式
    if args.play:
        print("随机播放模式(按Ctrl+C退出)...")
        try:
            while True:
                nplayer.playRandom()
                # 随机间隔（1/4, 1/2, 1, 2秒）
                rest = random.choice([0.25, 0.5, 1, 2])
                time.sleep(rest)
        except KeyboardInterrupt:
            sys.exit()
    
    # 钢琴演奏模式
    if args.piano:
        print("钢琴模式(使用A/S/D/F/G键演奏,关闭窗口退出)...")
        screen = pygame.display.set_mode((300, 200))  # 创建显示窗口
        pygame.display.set_caption("电子琴")
        
        # 按键映射（A/S/D/F/G对应C4/Eb/F/G/Bb）
        key_mapping = {
            pygame.K_a: 'C4',
            pygame.K_s: 'Eb4',
            pygame.K_d: 'F4',
            pygame.K_f: 'G4',
            pygame.K_g: 'Bb4'
        }
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in key_mapping:
                        note = key_mapping[event.key]
                        nplayer.play(f"{note}.wav")
            time.sleep(0.01)  # 降低CPU占用
        
        pygame.quit()
        sys.exit()
    
    # 和弦模式
    if args.chord:
        print("生成双音和弦(C4 + G, 延时0.1秒)...")
        chordData = generateChord(pmNotes['C4'], pmNotes['G4'], delay=0.1)
        writeWAVE('chord.wav', chordData)
        print("已生成 chord.wav")
        nplayer.add('chord.wav')
        nplayer.play('chord.wav')
        time.sleep(2)
    
    # 乐谱播放模式
    if args.playfile:
        print(f"播放乐谱文件:{args.playfile}")
        sequence = parseMusicFile(args.playfile)
        if sequence:
            nplayer.playSequence(sequence, bpm=120)
        else:
            print("无法读取乐谱文件")
        sys.exit()

if __name__ == '__main__':
    main()