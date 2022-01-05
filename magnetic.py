# QMC5883L
from statistics import mean, median, variance, stdev
import math
import time
import py_qmc5883l
sensor = py_qmc5883l.QMC5883L()
# xとyの最大最小値は事前に生データで計測して図っておく
MAX_X = 3855
MIN_X = -3480
MAX_Y = 1357
MIN_Y = -5020
SHOW_RAW = False


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


xmax = 0
xmin = 0
ymax = 0
ymin = 0
try:
    while True:
        # m = sensor.get_magnet()
        x, y = sensor.get_magnet()
        xmax = max(x, xmax)
        xmin = min(x, xmin)
        ymax = max(y, ymax)
        ymin = min(y, ymin)
        if not SHOW_RAW:
            capped_x = cap(x, MAX_X, MIN_X)
            capped_y = cap(y, MAX_Y, MIN_Y)
            norm_x = norm2(x, MAX_X, MIN_X)
            norm_y = norm2(y, MAX_Y, MIN_Y)
            print(
                f"X={round(norm_x,3)},\tY={round(norm_y,3)},\tC={round(calcDegree2(norm_x,norm_y),1)}")
        else:
            print(
                f"X={round(x,1)},\tY={round(y,1)},\tC={round(calcDegree2(x,y),1)}")
        # print(m, sensor.get_bearing(), calcDegree(*m))
        # print(sensor.get_bearing())
        time.sleep(0.1)
except KeyboardInterrupt:
    print(f"X max:{xmax}\t min:{xmin}")
    print(f"Y max:{ymax}\t min:{ymin}")
