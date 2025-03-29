import  random, argparse
import turtle, math
import numpy as np
from PIL import Image
from datetime import datetime
from math import gcd

class Spiro:
    '''构造函数'''
    def __init__(self, xc, yc, col, R, r, l):
        self.t = turtle.Turtle() # 创建一个新turtle对象
        self.t.shape('turtle') # 将光标形状设置为海龟
        self.step = 5 # 设置参数绘图角度为5度
        self.drawingComplete = False # 设置了一个绘制标志
        self.setparams(xc, yc, col, R, r, l) # 调用设置函数
        self.restart()
    
    def setparams(self, xc, yc, col, R, r, l):
        '''初始化Spiro对象'''
        self.xc = xc # 保存曲线中心的坐标
        self.yc = yc
        self.R = int(R) # 将每个圆的半径转换为整数并保存这些值
        self.r = int(r)
        self.l = l
        self.col = col
        gcdVal = gcd(self.r, self.R) # 计算半径的GCD
        self.nRot = self.r//gcdVal # 将GCD保存
        self.k = r/float(R)
        self.t.color(*col)
        self.a = 0 # 保存当前角度

    def restart(self):
        '''重置Spiro对象的绘制参数'''
        self.drawingComplete = False # 初始化绘制标志
        self.t.showturtle() # 显示海龟光标
        self.t.up() # 提笔
        R, k, l =self.R, self.k, self.l # 使用局部变量
        a = 0.0
        x = R*((1-k)*math.cos(a) + l*k*math.cos((1-k)*a/k)) # 计算a设为0时的x与y坐标
        y = R*((1-k)*math.sin(a) - l*k*math.sin((1-k)*a/k)) 
        self.t.setpos(self.xc + x, self.yc + y) # 获得曲线的起点
        self.t.down() # 落笔

    def draw(self):
        '''用连续的线段绘制曲线'''
        R, k, l = self.R, self.k, self.l
        for i in range(0, 360*self.nRot + 1, self.step): # 遍历参数i的完整范围
            a = math.radians(i)
            x = R*((1-k)*math.cos(a) + l*k*math.cos((1-k)*a/k)) # 计算参数i的每个值对应的X和Y坐标
            y = R*((1-k)*math.sin(a) - l*k*math.sin((1-k)*a/k))
            self.t.setpos(self.xc + x, self.yc + y)
        self.t.hideturtle() # 隐藏光标,完成绘制
    
    def update(self):
        '''创建动画'''
        if self.drawingComplete: # 检查绘制标志是否设置
            return
        self.a += self.step # 增加当前角度
        R, k, l = self.R, self.k, self.l
        a = math.radians(self.a) # 计算当前角度的x和y位置并将海龟移到那
        x = R*((1-k)*math.cos(a) + l*k*math.cos((1-k)*a/k))
        y = R*((1-k)*math.sin(a) - l*k*math.sin((1-k)*a/k))
        self.t.setpos(self.xc + x, self.yc + y)
        if self.a >= 360*self.nRot: # 检查角度是否达到这条特定曲线计算的完整范围
            self.drawingComplete =True # 如果是则设置绘制标志,绘图完成
            self.t.hideturtle()

class SpiroAnimator:
    '''绘制随机的螺线'''
    def __init__(self, N):
        self.deltaT = 10 # 设置定时器间隔
        self.width = turtle.window_width() # 保存海龟窗口的尺寸
        self.height = turtle.window_height()
        self.spiros = [] # 创建一个空数组,其中将填入一些Spiro对象封装
        for i in range(N):
            rparams = self.genRandomParams()
            spiro = Spiro(*rparams) # 创建一个Spiro对象,添加到对象的列表中
            self.spiros.append(spiro)
        turtle.ontimer(self.update, self.deltaT) # 每隔deltaT毫秒调用update
    
    def genRandomParams(self):
        '''生成随机参数'''
        width, height = self.width, self.height
        R = random.randint(50, min(width, height)//2) # 将R设置为50至窗口短边一半长度的随机整数
        r = random.randint(10, 9*R//10) # 将r设置为R的10%到90%之间
        l = random.uniform(0.1, 0.9)
        xc = random.randint(-width//2, width//2) # 在屏幕边界随机选择x和y坐标,作为螺线的中心
        yc = random.randint(-height//2, height//2)
        col = (random.random(),random.random(),random.random()) # 随机设置红、绿、蓝成分
        return (xc, yc, col, R, r, l) # 将所有参数作为一个元组返回
    
    def restart(self):
        '''重新启动程序'''
        for spiro in self.spiros: # 遍历所有Spiro对象
            spiro.clear()  # 清除绘制的每条螺线
            rparams = self.genRandomParams() # 分配新的螺线参数
            spiro.setparams(*rparams)
            spiro.restart() # 重新启动程序
    
    def update(self):
        '''更新所有的Spiro对象'''
        nComplete = 0 # 记录以画的spiro对象数目
        for spiro in self.spiros:
            spiro.update() # 更新它们
            if spiro.drawingComplete: # 如果一个spiro对象完成,计数器加1
                nComplete += 1
        if nComplete == len(self.spiros): # 如果所有对象都以画完,调用restart方法重新开始新的螺线动画
            self.restart()
        turtle.ontimer(self.update, self.deltaT) # 调用计时器方法,deltaT毫秒后再次调用update
    
    def toggleTurtles(self):
        '''打开或关闭海龟光标'''
        for spiro in self.spiros:
            if spiro.t.isvisible():
                spiro.t.hideturtle()
            else:
                spiro.t.showturtle()
    
def saveDrawing():
    '''将绘制保存为PNG图像'''
    turtle.hideturtle() # 隐藏海龟光标
    dateStr = (datetime.now()).strftime("%d%b%Y-%H%M%S") # 生成文件的唯一名称
    fileName = 'spiro-' + dateStr
    print('saving drawing to %s.eps/png' % fileName)
    canvas = turtle.getcanvas() # 将窗口保存为eps文件格式
    canvas.postscript(file = fileName + '.eps')
    img = Image.open(fileName + '.eps') # 将eps文件保存为png文件
    img.save(fileName + '.png', 'png')
    turtle.showturtle() # 取消隐藏海龟光标

def main():
    '''解析命令行参数和初始化'''
    print('generating spirograph...')
    descStr = """
    This program draws Spirographs using the Turtle module.
    When run with no arguments, this program draws randow Spirographs.

    Terminology:

    R: radius of outer circle
    r: radius of inner circle
    l: ratio of hole distance to r
    """
    parser = argparse.ArgumentParser(description=descStr) # 创建参数解析器对象
    parser.add_argument('--sparams', nargs=3, dest='sparams', required=False,
                        help='The three arguments in sparams: R, r, l.') # 添加可选参数
    args = parser.parse_args() # 调用函数进行实际的解析
    turtle.setup(width=0.8) # 将绘图窗口设置为80%屏幕宽度
    turtle.shape('turtle')
    turtle.title("Spirographs!")
    turtle.onkey(saveDrawing, "s") # 按下s时保存图画
    turtle.listen() # 监听用户事件
    turtle.hideturtle()
    if args.sparams: # 检查是否有参数赋给sparams
        params = [float(x) for x in args.sparams] # 如果有则从字符串中提取它们
        col = (0.0, 0.0, 0.0)
        spiro = Spiro(0, 0, col, *params) # 提取参数来构造Spiro对象
        spiro.draw() # 绘制螺线
    else: # 如果没有则进入随机模式
        spiroAnim = SpiroAnimator(4) # 创建一个spiroanimator对象
        turtle.onkey(spiroAnim.toggleTurtles, "t") # 捕捉按键t,切换海龟图标
        turtle.onkey(spiroAnim.restart, "space") # 处理空格,重新启动动画
    turtle.mainloop() # 保持tkinter窗口打开,监听事件

if __name__ == '__main__':
    main()

    