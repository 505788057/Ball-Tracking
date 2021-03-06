# 这一部分是使用霍夫变换的方法来写出小球的识别的
# 功能还未完全实现


from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
import tkinter as tk  # Python GUI
import tkinter.messagebox
from PIL import Image, ImageTk  # Python Imaging Library
# import kalman_new

vs = cv2.VideoCapture('C:/Users/50578/working/Ball-Tracking/BlueBal.avi')
# vs = cv2.VideoCapture(1, cv2.CAP_DSHOW)
vs.set(3, 1280)
vs.set(4, 720)
print("succeed.")
# time.sleep(1.0)

getPixelColor = False  # flag to get the pixel color of the ball when needed
camHeight = 1280
camWidth = 720
H, S, V = 0, 0, 0  # the color properties of the Pixel to track
mouseX, mouseY = 0, 0  # declare variables to capture mouse position for color tracking
lostballcount = 0
# 展示了系统控制面板
controllerWindow = tk.Tk()  # initializes this tk interpreter and creates the root window
controllerWindow.title("2DOF Ball-Plate Control Window ")  # define title of the root window
controllerWindow.geometry("1200x800")  # define size of the root window
controllerWindow["bg"] = "lightgrey"  # define the background color of the root window
controllerWindow.resizable(0, 0)  # define if the root window is resizable or not for Vertical and horizontal，不可以拉伸
# 主控制面板背景图片
# canvas = tk.Canvas(controllerWindow, width=1200,height=800,bd=0, highlightthickness=0)
# imgpath = 'background.gif'
# img = Image.open(imgpath)
# photo = ImageTk.PhotoImage(img)
# canvas.create_image(500, 20, image=photo)
# canvas.pack()
# 展示了实时画面的控制面板
videoWindow = tk.Toplevel(controllerWindow)  # a new window derived from the root window "controllerwindow"
videoWindow.title("Cam Footage")  # define title of videowindow
videoWindow.resizable(0, 0)  # Cannot resize the window
lmain = tk.Label(videoWindow)  # create an empty label widget in the videoWindow
lmain.pack()  # adjust the size of the videowindow to fit the label lmain
videoWindow.withdraw()  # hide the window
# 展示PID控制下输入输出的跟踪情况
graphWindow = tk.Toplevel(controllerWindow)  # a new window derived from the root window "graphwindow"
graphWindow.title("Position in function of time")  # define window title
graphWindow.resizable(0, 0)  # define if resizable or not
graphCanvas = tk.Canvas(graphWindow, width=500 + 200, height=camHeight)  # create a canvas widget in graphwindow
graphCanvas.pack()  # pack the canvas widget
graphWindow.withdraw()  # hide the graphwindow

# 声明一些滑条将用到的变量
sliderHDefault = 0
sliderSDefault = 0
sliderVDefault = 0
sliderCoefPDefault = 0.035
sliderCoefIDefault = 0.0
sliderCoefDDefault = 0.015
sliderRadiusDefault = 10
sliderSpeedDefault = 10
sliderRefXDefault = camWidth / 2
sliderRefYDefault = camHeight / 2

useKalmanBool = False


def UseKalmanJudge():  # function to judge weather use kalman filter or not.
    global useKalmanBool

    if useKalmanBool == False:
        useKalmanBool = True
        Bkalman["text"] = "Kalman Filter ON"
    else:
        useKalmanBool = False
        Bkalman["text"] = "Kalman Filter OFF"


# 验证小球运动的轨道
showCalqueCalibrationBool = False


def showCalqueCalibration():
    global showCalqueCalibrationBool
    showCalqueCalibrationBool = not showCalqueCalibrationBool


# 取色笔，可以获得像素点的HSV的值
def getMouseClickPosition(mousePosition):  # get mouse click position
    global mouseX, mouseY
    global getPixelColor
    mouseX, mouseY = mousePosition.x, mousePosition.y
    getPixelColor = True


# 用鼠标设定小球的运动位置，为其设定参考点
refY = 240  # reference refinate Y
refX = 240  # reference refinate X


def setRefWithMouse(mousePosition):
    global refX, refY
    if mousePosition.y > 10:
        refreshGraph()
        refX, refY = mousePosition.x, mousePosition.y


# 左上角，实时视频窗口，控制是不是要显示
showVideoWindow = False


def showCameraFrameWindow():  # function to toggle the showVideoWindow and change the label text of the button
    global showVideoWindow, showGraph
    global BShowVideoTxt
    if showVideoWindow == False:
        # if showGraph == True:
        #    graphWindow.withdraw()
        #    showGraph = False
        #    BShowGraph["text"] = "Show Plot"
        videoWindow.deiconify()
        showVideoWindow = True
        BShowVideo["text"] = "Hide Live CAM feed"
    else:
        videoWindow.withdraw()
        showVideoWindow = False
        BShowVideo["text"] = "Show Live CAM feed"


# 控制是否显示建模图。建模图显示了给定与输入输出之间的实时关系。
showGraph = False  # bool for Graph window


def showGraphWindow():  # function that toggles the Graph window and update the show graph button
    global showGraph, showVideoWindow
    global BShowGraph

    if showGraph == False:
        # if showVideoWindow == True:
        #    videoWindow.withdraw()
        #    showVideoWindow = False
        #    BShowVideo["text"] = "Show Live CAM feed"
        showGraph = True
        BShowGraph["text"] = "Hide Plot"
    else:
        showGraph = False
        BShowGraph["text"] = "Show Plot"


def refreshGraph():  # function that reset the time variable to 480 if the graph is full
    global t
    t = 480


# PID控制程序
def PIDcontrol():
    Kp = sliderCoefP.get()
    Ki = sliderCoefI.get()
    Kd = sliderCoefD.get()
    # print(Kp,Ki,Kd)


# 退出interface
def endProgam():
    controllerWindow.destroy()


# function that does nothing, may be used for delay
def donothing():
    pass


start_time = 0


def main():
    global H, S, V
    global getPixelColor
    global refX, refY, totalErrorX, totalErrorY
    global x, y, alpha, beta
    global prevX, prevY, prevAlpha, prevBeta, prevRefX, prevRefY
    global camWidth, camHeight
    global timeInterval, start_time
    global lostballcount
    start_time = time.time()


    _, frame = vs.read()
    time.sleep(0.05)
    # frame = frame[0:720, 280:1030]

    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, param1=130, param2=30, minRadius=15, maxRadius=38)

    cv2.circle(frame, (int(refX), int(refY)), int(4), (255, 0, 0), 2)
    if showCalqueCalibrationBool == True:
        cv2.circle(frame, (240, 240), 220, (255, 0, 0), 2)
        cv2.circle(frame, (240, 240), 160, (255, 0, 0), 2)
        cv2.line(frame, (240, 240), (240, 240 + 160), (255, 0, 0), 2)
        cv2.line(frame, (240, 240), (240 + 138, 240 - 80), (255, 0, 0), 2)
        cv2.line(frame, (240, 240), (240 - 138, 240 - 80), (255, 0, 0), 2)
    if circles is not None:
        for x, y, r in circles[0]:
            if r > 10:
                cv2.putText(frame, str(int(x)) + ";" + str(int(y)).format(0, 0), (int(x) - 50, int(y) - 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 255), 2)
                cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
                PIDcontrol()
                start_time = time.time()
        else:
            totalErrorX, totalErrorY = 0, 0
    else:
        lostballcount= lostballcount+1
        print('lost ball:',lostballcount)
    if showVideoWindow == True:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 转换颜色从BGR到RGB
        frame = Image.fromarray(frame)  # 将图像转换成Image对象
        imgtk = ImageTk.PhotoImage(image=frame)
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
    # timeInterval = time.time() - start_time
    # fps = int(1/timeInterval)
    # a = 0
    # a = a + 1
    # avefps = 0
    # avefps = (avefps + fps)/a
    # print(avefps)

    # 延迟5ms之后，进入主程序，从而形成循环。
    lmain.after(5, main)


'''
可以控制并改变HSV的上下值范围。
*************
here  ** 
      **
*************
      **
      **
*************
'''
FrameVideoControl = tk.LabelFrame(controllerWindow, text="Video Control")
FrameVideoControl.place(x=20, y=20, width=390)
EmptyLabel = tk.Label(FrameVideoControl)
EmptyLabel.pack()
BShowVideo = tk.Button(FrameVideoControl, text="Show Live CAM feed", command=showCameraFrameWindow)
BShowVideo.place(x=100, y=-5)
BPositionCalibration = tk.Button(FrameVideoControl, text="Toggle Calibration View", command=showCalqueCalibration)
BPositionCalibration.place(x=230, y=-5)

sliderUH = tk.Scale(FrameVideoControl, from_=-50, to=50, orient="horizontal", label="upper H", length=350,
                    tickinterval=10)
sliderUH.set(sliderHDefault)
sliderUH.pack()
sliderUS = tk.Scale(FrameVideoControl, from_=-50, to=50, orient="horizontal", label="upper S", length=350,
                    tickinterval=10)
sliderUS.set(sliderSDefault)
sliderUS.pack()
sliderUV = tk.Scale(FrameVideoControl, from_=-50, to=50, orient="horizontal", label="upper V", length=350,
                    tickinterval=10)
sliderUV.set(sliderVDefault)
sliderUV.pack()

sliderLH = tk.Scale(FrameVideoControl, from_=-50, to=50, orient="horizontal", label="lower H", length=350,
                    tickinterval=10)
sliderLH.set(sliderHDefault)
sliderLH.pack()
sliderLS = tk.Scale(FrameVideoControl, from_=-50, to=50, orient="horizontal", label="lower S", length=350,
                    tickinterval=10)
sliderLS.set(sliderSDefault)
sliderLS.pack()
sliderLV = tk.Scale(FrameVideoControl, from_=-50, to=50, orient="horizontal", label="lower V", length=350,
                    tickinterval=10)
sliderLV.set(sliderVDefault)
sliderLV.pack()
'''
系统控制，实现退出，连接等功能。
*************
      ** 
      **
*************
 here **
      **
*************
'''
FrameServosControl = tk.LabelFrame(controllerWindow, text="System Control")
FrameServosControl.place(x=20, y=580, width=390)
BQuit = tk.Button(FrameServosControl, text="Quit", command=endProgam)
BQuit.pack()
Bkalman = tk.Button(FrameServosControl, text="Kalman Filter OFF", command=UseKalmanJudge)
Bkalman.pack()

'''
控制PID参数
*************
      ** here
      **
*************
      **
      **
*************
'''
FramePIDCoef = tk.LabelFrame(controllerWindow, text="PID coefficients")
FramePIDCoef.place(x=420, y=20, width=380)
BShowGraph = tk.Button(FramePIDCoef, text="Plot on Graph", command=showGraphWindow)
BShowGraph.pack()
sliderCoefP = tk.Scale(FramePIDCoef, from_=0, to=0.1, orient="horizontal", label="P", length=350, tickinterval=0.01,
                       resolution=0.001)
sliderCoefP.set(sliderCoefPDefault)
sliderCoefP.pack()
sliderCoefI = tk.Scale(FramePIDCoef, from_=0, to=0.1, orient="horizontal", label="I", length=350, tickinterval=0.01,
                       resolution=0.001)
sliderCoefI.set(sliderCoefIDefault)
sliderCoefI.pack()
sliderCoefD = tk.Scale(FramePIDCoef, from_=0, to=0.1, orient="horizontal", label="D", length=350, tickinterval=0.01,
                       resolution=0.001)
sliderCoefD.set(sliderCoefDDefault)
sliderCoefD.pack()
'''
这一块是小球轨迹的控制程序，可以实现小球稳定在球面中心，画圆形，画8字型
*************
      ** 
      **
*************
      ** here
      **
*************
'''
FrameBallControl = tk.LabelFrame(controllerWindow, text="Ball Control")
FrameBallControl.place(x=420, y=350, width=380, height=200)

sliderRadius = tk.Scale(FrameBallControl, from_=0, to=300, orient="horizontal", label="Radius", length=350,
                        tickinterval=50, resolution=1)
sliderRadius.set(sliderRadiusDefault)
sliderRadius.pack()
sliderSpeed = tk.Scale(FrameBallControl, from_=0, to=20, orient="horizontal", label="Speed", length=350, tickinterval=1,
                       resolution=1)
sliderSpeed.set(sliderSpeedDefault)
sliderSpeed.pack()
BballDrawCircle = tk.Button(FrameBallControl, text="Enable Circle Trajectory", command=showCalqueCalibration)
BballDrawCircle.place(x=70, y=-5)
BballDrawEight = tk.Button(FrameBallControl, text="Enable Eight Trajectory", command=showCalqueCalibration)
BballDrawEight.place(x=220, y=-5)

# 获取鼠标的位置，转换成像素值。
# https://www.cnblogs.com/progor/p/8505599.html
videoWindow.protocol("WM_DELETE_WINDOW", donothing)
videoWindow.bind("<Button-3>", getMouseClickPosition)
videoWindow.bind("<Button-1>", setRefWithMouse)  # mouse click to set reference position

main()
tk.mainloop()
