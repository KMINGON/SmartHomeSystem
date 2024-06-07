# motion.py
import cv2

def getGrayCamImg(cam):
    """카메라로부터 그레이스케일 이미지를 캡처하는 함수"""
    ret, img = cam.read()
    if not ret:
        print("Failed to grab frame.")
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return gray

def diffImage(i):
    """세 이미지 간의 차이를 계산하는 함수"""
    diff0 = cv2.absdiff(i[0], i[1])
    diff1 = cv2.absdiff(i[1], i[2])
    return cv2.bitwise_and(diff0, diff1)

def updateCameraImage(cam, i):
    """카메라 이미지를 업데이트하는 함수"""
    i[0] = i[1]
    i[1] = i[2]
    i[2] = getGrayCamImg(cam)
