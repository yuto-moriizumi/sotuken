import logging
from threading import Thread
import time
import py_qmc5883l
import math


class Magnetic(Thread):
    """Magnetic Thread, provides course property [0,360)"""
    # xとyの最大最小値は事前に生データで計測して図っておく

    name = "Magnetic"
    daemon = True
    last_message = "loading"

    sensor = py_qmc5883l.QMC5883L()
    x = -1
    y = -1
    course = -1

    def calcDegree(self, x, y):
        """方位角を返す 真北0°、東90° 0-360 xとyは-1～1スケールで"""
        return (math.atan2(y, x)*(180/math.pi)+360) % 360

    def cap(self, value, MAX, MIN):
        """最大値と最小値でキャップする"""
        return min(max(value, MIN), MAX)

    def norm(self, value, MAX, MIN):
        """valueをMAXからMIN基準で-1から1にスケール"""
        z2o = (value-MIN)/(MAX-MIN)
        return self.cap(z2o*2-1, 1, -1)  # -1から1にスケール

    def __init__(self, max_x: int, min_x: int, max_y: int, min_y: int):
        Thread.__init__(self)
        self.MAX_X = max_x
        self.MIN_X = min_x
        self.MAX_Y = max_y
        self.MIN_Y = min_y

    def run(self):
        try:
            logger = logging.getLogger(__name__)
            log_count = 0  # 毎回ログ出力はせず、数回に1回にする
            while True:
                x, y = self.sensor.get_magnet()
                self.x = self.norm(x, self.MAX_X, self.MIN_X)
                self.y = self.norm(y, self.MAX_Y, self.MIN_Y)
                self.course = self.calcDegree(self.x, self.y)
                last_message = str(self.course)
                # if last_message != self.last_message:
                #     logger.info(last_message)
                self.last_message = last_message
                time.sleep(0.1)
                if log_count == 0:
                    logger.info(last_message)
                log_count = (log_count+1) % 10
        except:
            pass
