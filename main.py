'''这个要实现对脑波的实时读取与分析/脑波存储并做长期的分析'''
'''这是一个深入报神经研究的长期的项目'''
'''两种所需数据：小包：原始电位数据（快速）【底层】，大包：返回的脑波数据（一秒一次）【硬件解算过的】'''
#import bluetooth
import serial

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

def read_COM(COM, BAUD):#读取串口信息
    # 打开串口
    ser = serial.Serial(port=COM, baudrate=BAUD, timeout=1)#'COM3',9600串口号，波特率
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

def DATA(COM):#每秒一次的解析数据
    def value(a,b,c):#每三个值通过计算获取一个真正的值
        #左移
        shifted_a = int(a,16) << 16
        shifted_b = int(b,16) << 8#16是16进制
        c = int(c,16)
        # 或运算
        result = shifted_a | shifted_b | c
        return result
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
            Attention = data[56:58]#专注0-100
            Meditation = data[60:62]#放松0-100
            Chick_count = data[62:64]#校验和
            return Signal, Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, MiddleGamma, Attention, Meditation, Chick_count





'''下面是运行'''
while True:
    msg_data = read_COM('COM5',9600)#读取串口信息
    if DATA(msg_data) != None:#第513个数据包是校验位。如果不是没数据就输出
        Signal, Delta, Theta, LowAlpha, HighAlpha, LowBeta, HighBeta, LowGamma, MiddleGamma, Attention, Meditation, Chick_count = DATA(msg_data)
    HEX = COM2HEX(msg_data)
    if CHICK(int(HEX[0:2], 16),int(HEX[2:4], 16),int(HEX[4:6], 16)) == True:#校验位，用来忽略丢包。错误就重新获取
        rawdata = RAWDATA(HEX)






