import math
import serial
from servo import Servo
from time import sleep

# ser = serial.Serial(port='COM10', baudrate=115200, timeout=.1)
# def write_read(x):
# 	   ser.write(bytes(x, 'utf-8'))
# 	   sleep(0.05)
# 	   data = ser.readline()
# 	   return data

def Grab(isGrab):
    if isGrab:
        write_read("1")
    else:
        write_read("2")
    sleep(1)

# L1 = 179
# L2 = 176
L1 = 180
L2 = 175


def solve_ik(x, y, prefer_positive=True):
    """Возвращает (phi1, phi2) в градусах. prefer_positive — какой знак phi2 предпочесть."""
    r2 = x*x + y*y
    r = math.sqrt(r2)

    if r > L1 + L2 or r < abs(L1 - L2):
        return None

    c2 = (r2 - L1*L1 - L2*L2) / (2*L1*L2)
    c2 = max(-1.0, min(1.0, c2))
    phi2_abs = math.acos(c2)

    sign = +1 if prefer_positive else -1
    phi2 = sign * phi2_abs
    phi1 = math.atan2(y, x) - math.atan2(L2*math.sin(phi2),
                                         L1 + L2*math.cos(phi2))

    #return math.degrees(phi1), math.degrees(phi2)
    return round(phi1, 4), round(phi2, 4)

nullPos3 = 1106
def GoZ(mm):
    dir = 1
    if mm < 0:
        dir = -1
    s3.spin(5000*dir)
    sleep(abs(mm/6))
    s3.stop()

def Up(isUp, n=1):
    if isUp:
        # s3.move_to(nullPos3-1500)
        GoZ(-15)
    else:
        # s3.move_to(nullPos3 + 3200)
        GoZ(15)
        # s3.spin(5000)
        # sleep(tmGo)
        # s3.stop()
    sleep(1)

def moveTo(dist, dist2):

    s2.move_to(dist2, 1000, 200)
    s.move_to(dist, 1000, 200)
    sleep(1)
  
    s2.enable_torque()
    s.enable_torque()


def getShaska(isGet, n=1):
    if isGet:
        Up(False, n)
        Grab(1)
        Up(True, n)
    else:
        Up(False, n)
        Grab(0)
        Up(True, n)
def Security(angle1, angle2):
    # return (470<angle1<4095 and )
    if not(1500<angle1 < 3540):
        print("problem with angle1")
        return False
    elif not((0 < angle2 < 4096)):
        print("problem with angle2")
        return False
    else:
        return True
    # return (1622<angle1 < 3540) and(0 < angle2 < 4096)

shaskas = {}
def moveToPos(letter, pos):
    letters = ["А", "Б", "В", "Г", "Д", "Е"]
    # letter = input("Letter")
    if letter != "q" and letter in letters:
        # pos = int(input())
        print(letters.index(letter))
        x = (letters.index(letter)) * 26.5 + 13
        y = (8 - int(pos)) * 26.5 + 13

    else:
        x = int(letter)
        y = int(pos)

    print(x, y)

    cor_maxX = 11
    cor_maxY = 1
    x_max = 160
    y_max = 240
    x += round((x/x_max) * cor_maxX, 2)
    y += round((y/y_max) * cor_maxY, 2)
    x += x0
    y += y0

    r2 = x ** 2 + y ** 2
    r = math.sqrt(r2)
    if r > L1 + L2 or r < abs(L1 - L2):
        print("Точка недостижима: r =", r)
        return

   
    resCords = solve_ik(x, y, prefer_positive=True)
    resCords2 = solve_ik(x, y, prefer_positive=False)
    phi1 = resCords2[0]
    phi2 = resCords2[1]

    phi2 = round(math.radians(166+25/60) + phi2, 4)
    phi1 = round(math.radians(90)-phi1, 4)

    print(phi1, phi2)

    res = round(phi1 * 2048 / math.pi*(30/16))
    res2 = round(phi2 * 2048 / math.pi*(30/16))
    print(f"need m1-{nullPos1+res} m2 - {nullPos2-res2}")
    if Security(nullPos1+res, nullPos2-res2):
        moveTo(nullPos1+res, nullPos2-res2)
    else:
        print(f"promlem with angle1- {nullPos1+res} angle2 - {nullPos2-res2}")
    sleep(2)
    print(s.position()[0], s2.position()[0])


s = Servo(11, port='COM13') #arm 1 (от оси z)
s2 = Servo(2, port='COM13') #arm 2
s3= Servo(1, port='COM13') #ось z
sCam = Servo(10, port='COM13')

def isOnCam(isOnCam):
    if isOnCam:
        sCam.move_to(2175, 800)
    else:
        sCam.move_to(4096, 800)

nullPos1 = 1980
nullPos2 = 4095

x0 = 130
y0 = -65
# x0 = 102
# y0 = -29
a = int(input(""))
if a == 1:
    while True:
        xRes, yRes = input().split()
        print(xRes, yRes)
        moveToPos(xRes, yRes)
        Up(False)
        sleep(1)
        Up(True)
        break

elif a == 10:
    s.move_to(nullPos1)
    s2.move_to(nullPos2)
 
else:
    isOnCam(True)
    


