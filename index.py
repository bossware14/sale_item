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
import logging, ngrok
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
 
RL1 = 18 # ช่อง1
RL2 = 17 # ช่อง2
RL3 = 27 # ช่อง3
RL4 = 22 # ช่อง4

RL_COIN = 23 # เดเรย หยอดเหรียญ

GPIO_SENSOR = 5 # เซ็นเซอร์จับความเคลื่อนไหว
GPIO_COIN = 6 # เซ็นเซอร์ เครื่องหยอดเหรียญ

time_start = time.time()
time_end = time.time()
CHECK_COUNT = 0
RUN_CHECK = 0

looptime = 3.3
itemCount = 1

GPIO.setmode(GPIO.BCM)

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


def RUN_RELAY(number,itemCount):
     GPIO.setup(number,GPIO.OUT)
     time.sleep((looptime*itemCount))
     GPIO.setup(number,GPIO.IN)
     return True

item_list = [{
                    "id": 17,
                    "cate": "น้ำยาซักผ้า",
                    "name": "บรีสเอกเซลสูตรน้ำ",
                    "size": "25 มล.",
                    "image": "https://down-th.img.susercontent.com/file/th-11134207-7r98u-lqfr28j9qxnobc",
                    "price": "1"
                }, {
                    "id": 27,
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



@app.route('/rl')
def appRelay():
    rl_id = int(request.args.get('id'))
    if not rl_id:
        return jsonify({"status": "id"}), 200
    itemCount = int(request.args.get('count'))
    if not itemCount:
        return jsonify({"status": "count"}), 200
    RUN_RELAY(rl_id,itemCount)
    return jsonify({"status": "success"}), 200


MONEY = 0 
@app.route('/addcoin')
def addCoin():
    global MONEY
    coinsx = int(request.args.get('coin'))
    if not coinsx:
        return jsonify({"status": "error_is"}), 200
    MONEY = MONEY + coinsx
    return jsonify({"status": "success","MONEY":MONEY}), 200

@app.route('/getcoin')
def runCoin():
    global MONEY
    try:
        coins = int(request.args.get('coin'))
        if not coins:
           return jsonify({"status": "error_is"}), 200

        GPIO.setup(GPIO_COIN,GPIO.IN)
        CHECK_COUNT = 0
        #MONEY = 0
        while True:
            dist = SensorCoin()
            if CHECK_COUNT != 0  and CHECK_COUNT >= 10 :
              print("10 บาท")
              MONEY = MONEY + 10
              CHECK_COUNT = 0
              #return False
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
                 MONEY = MONEY - coins
                 return jsonify(MSG)
    except :
       print("Stopped")
       GPIO.cleanup()


if __name__ == '__main__':
    #try:
    socketio.run(app,host="0.0.0.0",port="5000", debug=False)
    #except :
    #    print("Measurement stopped by User")
     #   GPIO.cleanup()
    #socketio.run(app,host="0.0.0.0",port="5000", debug=True,ssl_context=('cert.pem', 'key.pem'))
