# QMC5883L
import math
import time
import qmc5883l

sensor = qmc5883l.QMC5883L()


def calcDegree(x, y):
    return 90-math.atan(y/x)*180/math.pi


# def bearingDegrees(headingDegrees):
#     bearing = 450 - headingDegrees
#     if (bearing >= 360):
#         bearing -= 360
#     return bearing


while True:
    # m = sensor.get_magnet()
    # print(m, sensor.get_bearing(), calcDegree(*m))
    # sensor.get_magnet()
    x, y, z = sensor.get_magnet()
    rad = math.atan2(y, x)
    deg = rad * (180 / math.pi)
    print(round(deg))
    time.sleep(0.1)
