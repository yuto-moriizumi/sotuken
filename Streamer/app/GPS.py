import logging
import micropyGPS
from threading import Thread


class GPS(Thread):
    """GPS Thread, provides lat, lon, alt, course"""
    gps: micropyGPS.MicropyGPS = None
    lat = -1
    lon = -1
    alt = -1
    course = -1
    name = "GPS"
    daemon = True
    last_message = "loading"

    def __init__(self, dummy=False):
        Thread.__init__(self)
        self.dummy = dummy

    def run(self):
        if self.dummy:
            while True:
                pass
        try:
            import serial  # check serial module existence
            # GPSモジュール初期化
            self.gps = micropyGPS.MicropyGPS(9, 'dd')  # MicroGPSオブジェクトを生成する。
            # 引数はタイムゾーンの時差と出力フォーマット
            s = serial.Serial('/dev/serial0', 9600, timeout=10)
            logger = logging.getLogger(__name__)
            while True:
                try:
                    sentence = s.readline().decode('utf-8')  # GPSデーターを読み、文字列に変換する
                    if sentence[0] != '$':  # 先頭が'$'でなければ捨てる
                        continue
                    for x in sentence:  # 読んだ文字列を解析してGPSオブジェクトにデーターを追加、更新する
                        self.gps.update(x)
                    if self.gps.clean_sentences > 20:  # ちゃんとしたデーターがある程度たまったら出力する
                        # h = self.gps.timestamp[0] if self.gps.timestamp[0] < 24 else self.gps.timestamp[0] - 24
                        # print('時刻:%2d:%02d:%04.1f' %
                        #       (h, gps.timestamp[1], gps.timestamp[2]))
                        isAvailable = True
                        lat = self.gps.latitude[0]  # 受信不良の場合は0になる
                        if lat != 0:  # 受信不良でないなら
                            self.lat = self.gps.latitude[0]
                            self.lon = self.gps.longitude[0]
                            self.alt = self.gps.altitude
                            self.course = self.gps.course
                        else:
                            isAvailable = False
                        self.last_message = '緯度:{0:2.8f}, 経度:{1:2.8f}, 海抜: {2:f}, 方位: {3:f}, 受信: {4}'.format(
                            self.lat, self.lon, self.alt, self.course, str(isAvailable))
                        logger.info(self.last_message)
                        # print('緯度:%2.8f, 経度:%2.8f, 海抜: %f, 方位: %f' %
                        #       (self.lat, self.lon, self.alt, self.course))
                        # print(f"利用衛星番号:{gps.satellites_used}")
                        # print('衛星番号: (仰角, 方位角, SN比)')
                        # print(gps.satellite_data)
                        # for k, v in deepcopy(gps.satellite_data.items()):
                        #     print('%d: %s' % (k, v))
                        # print('')
                except UnicodeDecodeError as e:
                    pass

        except ImportError:
            self.last_message = "[WARN] Serial module import error occured. GPS reader function disabled."
