# combined.py
import cv2
import time
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, Response, render_template_string, render_template, jsonify, redirect, url_for, request
import threading
from motion import getGrayCamImg, diffImage, updateCameraImage
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime
import requests

dhtDeviceIp = "192.168.122.109"
portnum = "8080"
dht_base_url = f"http://{dhtDeviceIp}:{portnum}"
dht_events_url = f"{dht_base_url}/dhtevents"

fireDeviceIp = "192.168.122.191"
fire_base_url = f"http://{fireDeviceIp}:{portnum}"
fire_events_url = f"{fire_base_url}/fireevents"

remoteDeviceIp = "192.168.122.20"
base_url = "http://" + remoteDeviceIp + ":" + portnum
light1_on_url = base_url + "/light1_on"
light1_off_url = base_url + "/light1_off"
door_open_url = base_url + "/open_door"
door_close_url = base_url + "/close_door"
light2_on_url = base_url + "/light2_on"
light2_off_url = base_url + "/light2_off"
window_open_url = base_url + "/open_window"
window_close_url = base_url + "/close_window"

app = Flask(__name__)

# 이메일 설정
smtp_server = "smtp.gmail.com"
port = 587
portssl = 465
userid = "rlaalsrhs59@gmail.com"
passwd = "nxeyqfrmnptoyuxz"

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
lock = threading.Lock()

surveillance_mode = False

def sendMail(image=None):
    """ 감지된 이미지를 이메일로 전송하는 함수 """
    to = [userid]
    msg = MIMEMultipart()
    if image is not None:
        imageByte = cv2.imencode(".jpeg", image)[1].tobytes()
        imageMime = MIMEImage(imageByte)
        msg['Subject'] = "집에 침입자 움직임이 감지되었습니다!!"
        msg.attach(imageMime)
    else:
        msg['Subject'] = "화재가 감지되었습니다!!"
        body = "Fire!!"
        msg.attach(MIMEText(body, 'plain'))

    
    msg['From'] = 'Me'
    msg['To'] = to[0]

    # SMTP 서버 연결 및 로그인
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo_or_helo_if_needed()
    ret, m = server.starttls()
    server.ehlo_or_helo_if_needed()
    ret, m = server.login(userid, passwd)
    
    if ret != 235:
        print("login fail")
        return

    # 이메일 전송
    server.sendmail('rlaalsrhs59@gmail.com', to, msg.as_string())
    server.quit()


def surveillance():
    """ 방범 기능을 수행하는 함수 """
    thresh = 50  # 움직임 감지 임계값
    global surveillance_mode

    if not cam.isOpened():
        print("cam isn't opened")
        return

    i = [None, None, None]
    flag = False

    # 초기 이미지 3프레임 캡처
    for n in range(3):
        with lock:
            i[n] = getGrayCamImg(cam)

    checkFlag = 0

    while True:
        with lock:
            diff = diffImage(i)
            thrimg = cv2.threshold(diff, thresh, 1, cv2.THRESH_BINARY)[1]
            count = cv2.countNonZero(thrimg)
        time.sleep(1)
        if not surveillance_mode:
            print('Surveillance mode OFF')
            continue
        print("count :", count)
        print("checkFlag :", checkFlag)
        # 침입자 감지 시
        if count > 1:
            checkFlag += 1
            if checkFlag >= 3 and not flag:
                sendMail(i[2])
                flag = True
                print("invader is coming!!!")
        elif count == 0 and flag:
            flag = False
            checkFlag = 0
        # 다음 이미지 처리
        with lock:
            updateCameraImage(cam, i)
        key = cv2.waitKey(10)
        if key == 27:  # ESC 키를 누르면 종료
            break

def generate_frames():
    """ 스트리밍을 위한 프레임 생성 함수 """
    while True:
        with lock:
            success, frame = cam.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/streaming')
def getstreaming():
    return render_template("camstreaming.html")

@app.route('/surveillance_on')
def surveillance_on():
    global surveillance_mode
    surveillance_mode = True
    return redirect(url_for('getstreaming'))

@app.route('/surveillance_off')
def surveillance_off():
    global surveillance_mode
    surveillance_mode = False
    return redirect(url_for('getstreaming'))

@app.route('/dhtevents')
def getevents():
    u = urlopen(dht_events_url)
    data=""
    try:
        #data = u.readlines()
        data = u.read()
        print(data)
    except HTTPError as e:
        print("HTTP error: %d" % e.code)
    except URLError as e:
        print("Network error: %s" % e.reason.args[1])

    return data

@app.route('/dht')
def getdht():
    return render_template("dhtchart.html")

def check_fire_status():
    try:
        response = requests.get(fire_events_url)
        data = response.json()
        if data.get("status") == "FIRE":
            print('fire!!')  # 화재 감지
            requests.get(door_close_url)
            requests.get(window_close_url)
            requests.get(light1_off_url)
            requests.get(light2_off_url)
            sendMail()
        else:
            print('no fire')  # 화재 미감지
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e.response.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"Network error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Request timed out: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        
def fire_status():
    while True:
        check_fire_status()
        time.sleep(1)  # 2초마다 확인
        
@app.route('/remote')
def getRemote():
    return render_template('remote.html')

@app.route('/light1_on')
def light1_on():
    requests.get(light1_on_url)
    return redirect(url_for('getRemote'))

@app.route('/light1_off')
def light1_off():
    requests.get(light1_off_url)
    return redirect(url_for('getRemote'))

@app.route('/light2_on')
def light2_on():
    requests.get(light2_on_url)
    return redirect(url_for('getRemote'))

@app.route('/light2_off')
def light2_off():
    requests.get(light2_off_url)
    return redirect(url_for('getRemote'))

@app.route('/door_open')
def door_open():
    requests.get(door_open_url)
    return redirect(url_for('getRemote'))

@app.route('/door_close')
def door_close():
    requests.get(door_close_url)
    return redirect(url_for('getRemote'))

@app.route('/window_open')
def window_open():
    requests.get(window_open_url)
    return redirect(url_for('getRemote'))

@app.route('/window_close')
def window_close():
    requests.get(window_close_url)
    return redirect(url_for('getRemote'))


if __name__ == '__main__':
    # 방범 기능을 별도의 쓰레드로 실행
    t = threading.Thread(target=surveillance)
    t.start()

    #fire Thread
    t1 = threading.Thread(target=fire_status)
    t1.start()
    # 웹 서  버 실행
    app.run(host='0.0.0.0', port=8080)
