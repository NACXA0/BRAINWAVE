'''这个要实现对脑波的实时读取与分析/脑波存储并做长期的分析'''
'''这是一个深入报神经研究的长期的项目'''
COM = 'COM5' #端口号
BAUD = 9600 #波特率

len_data = 25#大包同时显示数量
len_rawdata = 50#小包同时显示数量
save = False    #是否保存数据

DefaultName = 'BrainWaveData'   #一般不动。默认保存的文件名#如果不输入就是默认的
'''两种所需数据：小包：原始电位数据（快速）【底层】，大包：返回的脑波数据（一秒一次）【硬件解算过的】'''
#import bluetooth
import serial, time, matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

'''
def blue2COM():#蓝牙转串口
    # 寻找蓝牙设备
    devices = bluetooth.discover_devices()
    # 打印找到的设备列表
    for device in devices:
        print(device)
    # 连接到设备
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((device, 1))
    # 发送数据
    #data = "Hello, Bluetooth!"
    #sock.send(data)
    # 接收数据
    received_data = sock.recv(1024)
    print("Received: {}".format(received_data))
    return received_data
    # 断开连接
    #sock.close()
'''

def read_COM(com, baud):#读取串口信息
    # 打开串口
    ser = serial.Serial(port=com, baudrate=baud, timeout=1)#'COM3',9600串口号，波特率
    # 读取hex消息
    try:
        while True:
            # 读取字节流
            data = ser.read_all()
            # 将字节流转换为16进制字符串
            msg_data = data.hex()
            # 按照消息格式解析
            if len(msg_data) >= 8:
                #print("收到消息内容: ", msg_data)
                return msg_data
    except KeyboardInterrupt:
        ser.close()

def COM2HEX(COM):#串口信息转换成HEX格式读取
    for i in range(len(COM) - 10):#一次读取10个字节
        if COM[i:i + 10] == "aaaa048002":#读取标志位后面的内容
            return COM[i + 10:i + 16]#标志位后面的内容：第10个开始，第16个结束

def CHICK(High,Low, Chick):#校验位，用来忽略丢包
    sum = ((0x80 + 0x02 + High + Low) ^ 0xFFFFFFFF) & 0xFF
    if sum == Chick:
        return True
    else:
        return False

def RAWDATA(HEX):#原始数据
    High = int(HEX[0:2], 16)
    Low = int(HEX[2:4], 16)
    rawdata = (High << 8) | Low#前是High，后是Low
    if rawdata > 32768:
        rawdata -= 65536
    return rawdata


def value(a,b,c):#def DATA内部使用。每三个值通过计算获取一个真正的值
    #左移
    shifted_a = int(a,16) << 16
    shifted_b = int(b,16) << 8#16是16进制
    c = int(c,16)
    # 或运算
    result = shifted_a | shifted_b | c
    return result
def DATA(COM):#每秒一次的解析数据
    for i in range(len(COM) - 2):#一次读取2个字节
        if COM[i:i + 8] == "aaaa2002" and COM[i+62:i + 64] == "04" and COM[i+66:i + 68] == "05":#读取标志位后面的内容
            data = COM[i + 8:i + 72]#标志位后面的内容：第8个开始，第40个结束
            #print(data)
            Signal = int(data[0:2], 16)# 信号质量
            Delta = value(data[6:8],data[8:10],data[10:12])
            Theta = value(data[12:14],data[14:16],data[16:18])
            LowAlpha = value(data[18:20],data[20:22],data[22:24])
            HighAlpha = value(data[24:26],data[26:28],data[28:30])
            LowBeta = value(data[30:32],data[32:34],data[34:36])
            HighBeta = value(data[36:38],data[38:40],data[40:42])
            LowGamma = value(data[42:44],data[44:46],data[46:48])
            MiddleGamma = value(data[48:50],data[50:52],data[52:54])
            Attention = int(data[56:58], 16)#专注0-100
            try:#Meditation有时候会出现丢包，而且只有他.所以单独写一个
                Meditation = int(data[60:62], 16)#放松0-100
            except:
                Meditation = 0
                print('Meditation丢包')
            #Chick_count = data[62:64]#校验和.这个目前看来没有什么意义
            return Signal, Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, MiddleGamma, Attention, Meditation   #, Chick_count




#time = 0
y_rawdata = []
y_Signal = []
y_Delta = []
y_Theta = []
y_LowAlpha = []
y_HighAlpha = []
y_LowBeta = []
y_HighBeta = []
y_LowGamma = []
y_MiddleGamma = []
y_Attention = []
y_Meditation = []
x_data = [] #分别计数
x_rawdata = []  #分别计数
Signal, Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, MiddleGamma, Attention, Meditation = 0,0,0,0,0,0,0,0,0,0,0


'''下面是读取数据'''
#1准备保存文件

if save == True:
    columns = ['rowdata', 'Signal', 'Delta', 'Theta', 'LowAlpha', 'HighAlpha', 'LowBeta', 'HighBeta', 'LowGamma',
               'MiddleGamma', 'Attention', 'Meditation']
    name = input("请输入要保存的文件名(默认为BrainWaveData)：")
    df = pd.DataFrame(columns=columns)
    if name == '':
        name = DefaultName


#读取数据
while True:
    #0绘图准备
    '''直接在程序里面绘图'''
    # matplotlib.rcParams['font.sans - serif']=['SimHei']#用来正常显示中文标签
    # 创建绘制实时损失的动态窗口
    plt.ion()


    #1读取串口信息
    msg_data = read_COM(COM, BAUD)#读取串口信息
    #2当获取到大数据包时的操作+数据准备
    if DATA(msg_data) != None:#第513个数据包是校验位。如果不是没数据就输出
        print('AAAAAAAAAAAA')
        x_data.append(time.time())  # X横轴是时间.这个是大数据包的时间

        Signal, Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, MiddleGamma, Attention, Meditation = DATA(msg_data)
        print(Signal, Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, MiddleGamma, Attention, Meditation)
        # 如果有数据的话就添加上
        y_Signal.append(Signal)
        y_Delta.append(Delta)
        y_Theta.append(Theta)
        y_LowAlpha.append(LowAlpha)
        y_HighAlpha.append(HighAlpha)
        y_LowBeta.append(LowBeta)
        y_HighBeta.append(HighBeta)
        y_LowGamma.append(LowGamma)
        y_MiddleGamma.append(MiddleGamma)
        y_Attention.append(Attention)
        y_Meditation.append(Meditation)

        if len(x_data) > len_data:  # 限制x轴的长度。根据某个横轴的值判断。如果数据多了就去掉第一个#柱状图不需要列表的形式
            x_data.pop(0)
            y_Signal.pop(0)
            y_Delta.pop(0)
            y_Theta.pop(0)
            y_LowAlpha.pop(0)
            y_HighAlpha.pop(0)
            y_LowBeta.pop(0)
            y_HighBeta.pop(0)
            y_LowGamma.pop(0)
            y_MiddleGamma.pop(0)
            y_Attention.pop(0)
            y_Meditation.pop(0)

        plt.clf()  # 清除之前画的图
        #1总体实时柱状图
        y = [Signal, Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, MiddleGamma, Attention, Meditation]
        x = ['Signal', 'Delta', 'Theta', 'LowAlpha', 'HighAlpha', 'LowBeta', 'HighBeta', 'LowGamma', 'MiddleGamma', 'Attention', 'Meditation']
        plt.subplot(3, 4, 2)#1行1列第二个
        plt.bar(x, y)#柱状图：所有的数据都在一个图里面的实时数据
        #各个折线
        plt.subplot(3, 4, 3)#1行2列第三个
        plt.plot(x_data, y_Delta, label='Delta')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 4)
        plt.plot(x_data, y_Theta, label='Theta')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 5)
        plt.plot(x_data, y_LowAlpha, label='LowAlpha')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 6)
        plt.plot(x_data, y_HighAlpha, label='HighAlpha')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 7)
        plt.plot(x_data, y_LowBeta, label='LowBeta')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 8)
        plt.plot(x_data, y_HighBeta, label='HighBeta')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 9)
        plt.plot(x_data, y_LowGamma, label='LowGamma')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 10)
        plt.plot(x_data, y_MiddleGamma, label='MiddleGamma')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 11)
        plt.plot(x_data, y_Attention, label='Attention')  # 折线图：包含历史的趋势变化
        plt.subplot(3, 4, 12)
        plt.plot(x_data, y_Meditation, label='Meditation')  # 折线图：包含历史的趋势变化

    #3对小数据包的操作+数据准备
    HEX = COM2HEX(msg_data)
    if CHICK(int(HEX[0:2], 16),int(HEX[2:4], 16),int(HEX[4:6], 16)) == True:#校验位，用来忽略丢包。错误就重新获取
        x_rawdata.append(time.time())  # X横轴是时间.这个是小数据包的时间
        rawdata = RAWDATA(HEX)
        y_rawdata.append(rawdata)#添加原始数据到列表
        if len(y_rawdata) > len_rawdata:  # 限制x轴的长度。根据某个横轴的值判断
            x_rawdata.pop(0)
            y_rawdata.pop(0)
        plt.subplot(3, 4, 1)#1行1列第一个
        plt.plot(x_rawdata, y_rawdata * np.array([-1]))  # 小数据包绘制。画出当前x列表和y列表中的值的图形

        plt.pause(0.001)  # 暂停一段时间，不然画的太快会卡住显示不出来
        plt.show()  # 更新图像.否则一会就会卡死
        # plt.ioff()  # 关闭画图窗口

'''2添加并另存为csv'''


if save == True:
    df = df.append(list, ignore_index=True)
    df.to_csv(name+'.csv')
