# QMC5883L
from statistics import mean, median, variance, stdev
import math
import time
import py_qmc5883l
sensor = py_qmc5883l.QMC5883L()
# xとyの最大最小値は事前に生データで計測して図っておく
MAX_X = 1397
MIN_X = -5132
MAX_Y = -7455
MIN_Y = -13355


def calcDegree(x, y):
    return 90-math.atan(y/x)*180/math.pi


# 方位角を返す 真北0°、東90° 0-360
def calcDegree2(x, y):
    return (math.atan2(y, x)*(180/math.pi)+360) % 360


def cap(value, MAX, MIN):
    return min(max(value, MIN), MAX)


def norm(value, MAX, MIN):
    return (value-mean([MAX, MIN]))/stdev([MAX, MIN])


def norm2(value, MAX, MIN):
    # 0-1にスケール
    z2o = (value-MIN)/(MAX-MIN)
    return cap(z2o*2-1, 1, -1)  # -1から1にスケール


while True:
    # m = sensor.get_magnet()
    x, y = sensor.get_magnet()
    capped_x = cap(x, MAX_X, MIN_X)
    capped_y = cap(y, MAX_Y, MIN_Y)
    norm_x = norm2(x, MAX_X, MIN_X)
    norm_y = norm2(y, MAX_Y, MIN_Y)
    print(f"{norm_x},{norm_y},{calcDegree2(norm_x,norm_y)}")
    # print(m, sensor.get_bearing(), calcDegree(*m))
    # print(sensor.get_bearing())
    time.sleep(0.1)
