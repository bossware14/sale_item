from flask import Flask, request, jsonify, render_template,send_file 
from flask_socketio import SocketIO, emit, send
from flask_cors import CORS, cross_origin
import requests
import gpiod
import subprocess
import os
import time
import json
from datetime import datetime, timezone, timedelta
import socket
import uuid
from gpiozero import MotionSensor , AngularServo , LED ,Servo
from signal import pause

import RPi.GPIO  as GPIO
import threading
import math
from time import sleep, localtime

#    pip install flask flask-socketio gpiod
#    pip install gunicorn
app = Flask(__name__,template_folder="")
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
CORS(app)
 
RL1 = 23 # ช่อง1
RL2 = 17 # ช่อง2
RL3 = 27 # ช่อง3
RL4 = 22 # ช่อง4

RL_COIN = 5 # เดเรย หยอดเหรียญ
SPIN_SENSOR = 12
GPIO_COIN = 6 # เซ็นเซอร์ เครื่องหยอดเหรียญ

time_start = time.time()
time_end = time.time()
CHECK_COUNT = 0
RUN_CHECK = 0

looptime = 3#2.68
itemCount = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(RL1,GPIO.IN)
GPIO.setup(RL2,GPIO.IN)
GPIO.setup(RL3,GPIO.IN)
GPIO.setup(RL4,GPIO.IN)
GPIO.setup(SPIN_SENSOR,GPIO.IN)
IS_FILE = 0
IS_RUN = 0
def my_callback(channel):
  global IS_RUN,IS_FILE
  if IS_RUN != 0 and IS_FILE != 0 :
    if GPIO.input(channel) == 1 and GPIO.input(IS_RUN) == 1:
       print("Input ON/ON")
    if GPIO.input(channel) == 0 and GPIO.input(IS_RUN) == 0:
       print("Input OFF/OFF")
    if GPIO.input(channel) == 0 and GPIO.input(IS_RUN) == 1:
       print("Input OFF/ON")
       IS_FILE = IS_FILE - 1
       LCD_NUMBER(IS_FILE)
       time.sleep(1)
       if IS_FILE <= 0 :
          GPIO.setup(IS_RUN,GPIO.IN)
          IS_RUN = 0
    time.sleep(0.1)

    #print("Input detected")
GPIO.add_event_detect(SPIN_SENSOR, GPIO.FALLING, callback=my_callback)

def RUN_RELAY(number,itemCount):
     global IS_RUN,IS_FILE
     IS_RUN = number
     IS_FILE = itemCount
     LCD_NUMBER(IS_FILE)
     GPIO.setup(number,GPIO.OUT)
     #time.sleep((looptime*itemCount))
     #GPIO.setup(number,GPIO.IN)
     return True


def checkSensor(numc):
    while  GPIO.input(numc) == 0:
        pulse_start = True
        time_start = time.time()
    while GPIO.input(numc) == 1:
        pulse_start = False
        time_end = time.time()

    MYSO = time_end-time_start
    print(MYSO)
    return MYSO

def SensorCoin():
    global CHECK_COUNT,time_start, time_end,RUN_CHECK
    distance = 1
    while  GPIO.input(GPIO_COIN) == 0:
        pulse_start = True
        time_start = time.time()
    while GPIO.input(GPIO_COIN) == 1:
        pulse_start = False
        time_end = time.time()
    if pulse_start == False and round(time_end-time_start) < 0 :
        pulse_start = "None"
        RUN_CHECK = RUN_CHECK + 1
        print(RUN_CHECK)
    if pulse_start == False and round(time_end-time_start) > 0 :
        RUN_CHECK = 0
    return pulse_start



item_list = [{
                    "id": 23,
                    "cate": "น้ำยาซักผ้า",
                    "name": "บรีสเอกเซลสูตรน้ำ",
                    "size": "25 มล.",
                    "image": "https://down-th.img.susercontent.com/file/th-11134207-7r98u-lqfr28j9qxnobc",
                    "price": "1"
                }, {
                    "id": 17,
                    "cate": "น้ำยาปรับผ้านุ่ม",
                    "name": "ดาวน์นี่ ซันไรซ์เฟรช",
                    "size": "20 มล.",
                    "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWVgRqZfhzKI9rRpb0-2J0FfpY6MzsX9aHNkT26Ur7xQ&s",
                    "price": "1"
                }]


if os.path.isfile('data.json'):
    with open('data.json', 'r') as f:
      json_data = json.load(f)
else:
    json_data = {}
    with open('data.json', 'w') as f:
      json.dump(json_data, f) 
 
@app.route('/')
def index():
    return render_template('index.html')

@socketio.event()
def my_event(message):
    emit('response', {'data':'got it!'})

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP



#ฟังชั้น เขียนไฟล์
def update_data(json_data):
    tz = timezone(timedelta(hours = 7))
    json_data['time'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    with open('data.json', 'w') as f:
        json.dump(json_data, f) 
    return json_data


def getItem(key,value):
  try:
    message = "send"
    print(message)
    return send(message, broadcast=True)
  finally:
    message = "success"
    print(message)
    return send(message, broadcast=True)

tz = timezone(timedelta(hours = 7))

def createQR(money):
    message = {}
    message['msg'] = 'createQR'
    message['status'] = 'success'
    message['time'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    headers = {"Content-Type": "application/json"}
    url = str("https://ap.all123th.com/api?Agent=BR&amount="+str(money)+"&username=APP_AUTO&device=&type=")
    resq = requests.get(url, headers=headers)
    jsona = resq.json()
    message['status'] = jsona["status"]
    message['img'] = jsona["img"]
    message['refId'] = jsona["refId"]
    message['amount'] = jsona["amount"]
    message['ref'] = jsona["ref"]
    message['ref1'] = jsona["ref1"]
    message['ref2'] = jsona["ref2"]
    message['url'] = jsona["url"]
    message['qrcode'] = jsona["qrcode"]
    print(message)
    return send(message, broadcast=True)

def checkRef(refId):
    message = {}
    message['msg'] = 'checkRef'
    message['status'] = 'success'
    message['time'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    headers = {"Content-Type": "application/json"}
    url = str("https://api.all123th.com/payment-swiftpay/"+str(refId))
    resq = requests.get(url, headers=headers)
    jsona = resq.json()
    message['refId'] = jsona["data"]["refId"]
    message['status'] = jsona["data"]["status"]
    message['msg'] = jsona["data"]["msg"]
    print(message)
    return send(message, broadcast=True)


def getGpio(gpioId,count):
    message = {}
    message['msg'] = 'running'
    message['status'] = 'success'
    message['gpioId'] = gpioId
    message['count'] = count
    print("running")
    return message


def topup(money):
  try:
    message = {}
    message['msg'] = 'running'
    message['status'] = 'success'
    message['time'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    print(message)
    return send(message, broadcast=True)
  finally:
    time.sleep(5)
    message = {}
    message['msg'] = 'success'
    message['status'] = 'success'
    message['time'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    print(message)
    return send(message, broadcast=True)

@app.route('/item')
def get_item():
    return item_list,200

@app.route('/gpio')
def get_gpio():
    d_id = request.args.get('id')
    if not d_id:
        return jsonify({"status": "error_is"}), 200
    d_val = request.args.get('count')
    if not d_val:
        return jsonify({"status": "error_count"}), 200
    getGpio(d_id,d_val)
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "ok"
    return jsonify(msg),200



#API
@app.route('/api')
def get_api():
    tz = timezone(timedelta(hours = 7))
    json_data['time'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    return update_data(json_data),200
#SOCKET
@socketio.on('message')
def handleMessage(msg):
    if msg == 'connect':
        return send(update_data(json_data), broadcast=True)
    else:
       res = json.loads(msg)
       print(res)

       if res["status"] == 'action' and res['key'] == 'createQR': 
          print(res["data"])
          return createQR(res["value"])

       if res["status"] == 'action' and res['key'] == 'checkRef': 
          return checkRef(res["value"])

       if res["status"] == 'action' and res['key'] == 'sendItem': 
          message = "sendItems"
          #print(res["value"])
          for x in json.loads(res["value"]) :
            if x is None:
                print("None")
            #   getGpio(x["id"], x["value"])
            else: 
              send(getGpio(x["id"],x["value"]), broadcast=True)

          return send(message, broadcast=True)

       if res["status"] == 'action' and res['key'] == 'load' : 
          message = "ok"
          return topup(res["value"])
          return send(message, broadcast=True)

       if res["status"] == 'message': # status = message
          return send(update_data(json_data), broadcast=True)

       if res["status"] == 'update':
          json_data[res["key"]] = res["value"]
          return send(update_data(json_data), broadcast=True)

       return send(json_data, broadcast=True)

@socketio.on_error()
def error_handler(e):
    print(f'An error occurred: {e}')


HexDigits = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 
            0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71, 0x3D, 0x76, 
            0x06, 0x1E, 0x76, 0x38, 0x55, 0x54, 0x3F, 0x73, 0x67, 
            0x50, 0x6D, 0x78, 0x3E, 0x1C, 0x2A, 0x76, 0x6E, 0x5B,
            0x00, 0x40, 0x63, 0xFF]

ADDR_AUTO = 0x40
ADDR_FIXED = 0x44
STARTADDR = 0xC0
# DEBUG = False

class TM1637:
    __doublePoint = False
    __Clkpin = 0
    __Datapin = 0
    __brightness = 1.0  # default to max brightness
    __currentData = [0, 0, 0, 0]

    def __init__(self, CLK, DIO, brightness):
        self.__Clkpin = CLK
        self.__Datapin = DIO
        self.__brightness = brightness
        GPIO.setup(self.__Clkpin, GPIO.OUT)
        GPIO.setup(self.__Datapin, GPIO.OUT)

    def cleanup(self):
        """Stop updating clock, turn off display, and cleanup GPIO"""
        self.StopClock()
        self.Clear()
        GPIO.cleanup()

    def Clear(self):
        b = self.__brightness
        point = self.__doublePoint
        self.__brightness = 0
        self.__doublePoint = False
        data = [0x7F, 0x7F, 0x7F, 0x7F]
        self.Show(data)
        # Restore previous settings:
        self.__brightness = b
        self.__doublePoint = point

    def ShowInt(self, i):
        s = str(i)
        self.Clear()
        for i in range(0, len(s)):
            self.Show1(i, int(s[i]))

    def Show(self, data):
        for i in range(0, 4):
            self.__currentData[i] = data[i]

        self.start()
        self.writeByte(ADDR_AUTO)
        self.br()
        self.writeByte(STARTADDR)
        for i in range(0, 4):
            self.writeByte(self.coding(data[i]))
        self.br()
        self.writeByte(0x88 + int(self.__brightness))
        self.stop()

    def Show1(self, DigitNumber, data):
        """show one Digit (number 0...3)"""
        if(DigitNumber < 0 or DigitNumber > 3):
            return  # error

        self.__currentData[DigitNumber] = data

        self.start()
        self.writeByte(ADDR_FIXED)
        self.br()
        self.writeByte(STARTADDR | DigitNumber)
        self.writeByte(self.coding(data))
        self.br()
        self.writeByte(0x88 + int(self.__brightness))
        self.stop()
    # Scrolls any integer n (can be more than 4 digits) from right to left display.
    def ShowScroll(self, n):
        n_str = str(n)
        k = len(n_str)

        for i in range(0, k + 4):
            if (i < k):
                self.Show([int(n_str[i-3]) if i-3 >= 0 else None, int(n_str[i-2]) if i-2 >= 0 else None, int(n_str[i-1]) if i-1 >= 0 else None, int(n_str[i]) if i >= 0 else None])
            elif (i >= k):
                self.Show([int(n_str[i-3]) if (i-3 < k and i-3 >= 0) else None, int(n_str[i-2]) if (i-2 < k and i-2 >= 0) else None, int(n_str[i-1]) if (i-1 < k and i-1 >= 0) else None, None])
            sleep(1)

    def SetBrightness(self, percent):
        """Accepts percent brightness from 0 - 1"""
        max_brightness = 7.0
        brightness = math.ceil(max_brightness * percent)
        if (brightness < 0):
            brightness = 0
        if(self.__brightness != brightness):
            self.__brightness = brightness
            self.Show(self.__currentData)

    def ShowDoublepoint(self, on):
        """Show or hide double point divider"""
        if(self.__doublePoint != on):
            self.__doublePoint = on
            self.Show(self.__currentData)

    def writeByte(self, data):
        for i in range(0, 8):
            GPIO.output(self.__Clkpin, GPIO.LOW)
            if(data & 0x01):
                GPIO.output(self.__Datapin, GPIO.HIGH)
            else:
                GPIO.output(self.__Datapin, GPIO.LOW)
            data = data >> 1
            GPIO.output(self.__Clkpin, GPIO.HIGH)
 
        # wait for ACK
        GPIO.output(self.__Clkpin, GPIO.LOW)
        GPIO.output(self.__Datapin, GPIO.HIGH)
        GPIO.output(self.__Clkpin, GPIO.HIGH)
        GPIO.setup(self.__Datapin, GPIO.IN)

        while(GPIO.input(self.__Datapin)):
            sleep(0.001)
            if(GPIO.input(self.__Datapin)):
                GPIO.setup(self.__Datapin, GPIO.OUT)
                GPIO.output(self.__Datapin, GPIO.LOW)
                GPIO.setup(self.__Datapin, GPIO.IN)
        GPIO.setup(self.__Datapin, GPIO.OUT)

    def start(self):
        """send start signal to TM1637"""
        GPIO.output(self.__Clkpin, GPIO.HIGH)
        GPIO.output(self.__Datapin, GPIO.HIGH)
        GPIO.output(self.__Datapin, GPIO.LOW)
        GPIO.output(self.__Clkpin, GPIO.LOW)

    def stop(self):
        GPIO.output(self.__Clkpin, GPIO.LOW)
        GPIO.output(self.__Datapin, GPIO.LOW)
        GPIO.output(self.__Clkpin, GPIO.HIGH)
        GPIO.output(self.__Datapin, GPIO.HIGH)

    def br(self):
        """terse break"""
        self.stop()
        self.start()

    def coding(self, data):
        if(self.__doublePoint):
            pointData = 0x80
        else:
            pointData = 0

        if(data == 0x7F or data is None):
            data = 0
        else:
            data = HexDigits[data] + pointData
        return data

    def clock(self, military_time):
        """Clock script modified from: https://github.com/johnlr/raspberrypi-tm1637"""
        self.ShowDoublepoint(True)
        while (not self.__stop_event.is_set()):
            t = localtime()
            hour = t.tm_hour
            if not military_time:
                hour = 12 if (t.tm_hour % 12) == 0 else t.tm_hour % 12
            d0 = hour // 10 if hour // 10 else 36
            d1 = hour % 10
            d2 = t.tm_min // 10
            d3 = t.tm_min % 10
            digits = [d0, d1, d2, d3]
            self.Show(digits)
            # # Optional visual feedback of running alarm:
            # print digits
            # for i in tqdm(range(60 - t.tm_sec)):
            for i in range(60 - t.tm_sec):
                if (not self.__stop_event.is_set()):
                    sleep(1)

    def StartClock(self, military_time=True):
        # Stop event based on: http://stackoverflow.com/a/6524542/3219667
        self.__stop_event = threading.Event()
        self.__clock_thread = threading.Thread(
            target=self.clock, args=(military_time,))
        self.__clock_thread.start()

    def StopClock(self):
        try:
            print ('Attempting to stop live clock')
            self.__stop_event.set()
        except:
            print ('No clock to close')

def LCDOFF():
    display = TM1637(CLK=21, DIO=20, brightness=1.0)
    display.Clear()



#LEDNUMBER
def LCD_NUMBER(scrap1):
 
    display = TM1637(CLK=21, DIO=20, brightness=1.0)
    display.Clear()
    if int(scrap1) >= 1000 :
       splitx = list(str(scrap1))
       display.Show1(1, int(splitx[1]))
       display.Show1(2, int(splitx[2]))
       display.Show1(3, int(splitx[3]))
       display.Show1(0, int(splitx[0]))
       return True
    if int(scrap1) >= 100 :
       splitx = list(str(scrap1))
       display.Show1(1, int(splitx[0]))
       display.Show1(2, int(splitx[1]))
       display.Show1(3, int(splitx[2]))
    else:
        if int(scrap1) >= 10 :
         splitx = list(str(scrap1))
         display.Show1(2, int(splitx[0]))
         display.Show1(3, int(splitx[1]))
        else:
          display.Show1(3, int(scrap1))

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

@app.route('/lcd',methods=['GET'])
def lcd_view():
    count = request.args.get('number')
    if not count:
        LCDOFF()
        return jsonify({"status": "error"}), 200
    LCD_NUMBER(count)
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "ok"
    return jsonify(msg),200

@app.route('/rl')
def appRelay():
    rl_id = int(request.args.get('id'))
    if not rl_id:
        return jsonify({"status": "id"}), 200
    itemCount = int(request.args.get('count'))
    if not itemCount:
        return jsonify({"status": "count"}), 200
    #LCD_NUMBER()
    #time.sleep(1)
    LCD_NUMBER(itemCount)
    RUN_RELAY(rl_id,itemCount)
    LCDOFF()
    return jsonify({"status": "success"}), 200


MONEY = 0 
@app.route('/addcoin')
def addCoin():
    global MONEY
    coinsx = int(request.args.get('coin'))
    if not coinsx:
        return jsonify({"status": "error_is"}), 200
    MONEY = MONEY + coinsx
    LCD_NUMBER(MONEY)
    
    return jsonify({"status": "success","MONEY":MONEY}), 200

#GPIO.setup(RL_COIN,GPIO.IN)
GPIO.setup(RL_COIN,GPIO.OUT)
GPIO.setup(GPIO_COIN,GPIO.IN)
@app.route('/getcoin')
def runCoin():
    global MONEY
    try:
        coins = int(request.args.get('coin'))
        if not coins:
           return jsonify({"status": "error_is"}), 200
#        rl_id = int(request.args.get('id'))
#        if not rl_id:
#           return jsonify({"status": "id"}), 200
#        itemCount = int(request.args.get('count'))
#        if not itemCount:
#           return jsonify({"status": "count"}), 200

        CHECK_COUNT = 0
        #GPIO.setup(RL_COIN,GPIO.OUT)
        #MONEY = 0
        while True:
            dist = SensorCoin()
            #
            if CHECK_COUNT != 0  and CHECK_COUNT >= 10 :
              print("10 บาท")
              MONEY = MONEY + 10
              CHECK_COUNT = 0
              #LCD_NUMBER(MONEY)
              print(CHECK_COUNT)
            if dist == True: 
              CHECK_COUNT = CHECK_COUNT +1
              time.sleep(0.09)
            else:
              if dist == False and CHECK_COUNT != 0  and CHECK_COUNT == 1 and round(time_end-time_start) > 0:
                print("1 THB")
                MONEY = MONEY + 1
                CHECK_COUNT = 0
                #return False
              if dist == False and CHECK_COUNT != 0 and round(time_end-time_start) < 0:
                CHECK_COUNT = 0
                print("Clear")
              if dist == False and CHECK_COUNT != 0 and CHECK_COUNT < 10 and CHECK_COUNT >= 5 and round(time_end-time_start) > 0:
                print("5 THB")
                MONEY = MONEY + 5
                CHECK_COUNT = 0
                #return False
              if coins <= MONEY :
                 MSG = {}
                 MSG['status'] = "success"
                 MSG['MONRY'] = MONEY
                 MONEY = 0
                 #RUN_RELAY(rl_id,itemCount)
                 return jsonify(MSG)
    except :
       print("Stopped")
       #GPIO.cleanup()

LCD_NUMBER(0)

if __name__ == '__main__':
    #try:
    socketio.run(app,host="0.0.0.0",port="5000", debug=False)
    #except :
    #    print("Measurement stopped by User")
     #   GPIO.cleanup()
    #socketio.run(app,host="0.0.0.0",port="5000", debug=True,ssl_context=('cert.pem', 'key.pem'))