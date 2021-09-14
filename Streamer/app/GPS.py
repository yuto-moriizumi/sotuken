import micropyGPS
from threading import Thread


class GPS(Thread):
    """GPS Thread, provides lat, lon, alt, course"""
    gps: micropyGPS.MicropyGPS = None
    lat = -1
    lon = -1
    alt = -1
    course = -1

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.name = "GPS"

    def run(self):
        try:
            import serial  # check serial module existence
            # GPSモジュール初期化
            self.gps = micropyGPS.MicropyGPS(9, 'dd')  # MicroGPSオブジェクトを生成する。
            # 引数はタイムゾーンの時差と出力フォーマット
            gpsthread = Thread(
                target=self.rungps)  # 上の関数を実行するスレッドを生成
            gpsthread.daemon = True
            gpsthread.start()  # スレッドを起動
        except ImportError:
            print(
                "[WARN] Serial module import error occured. GPS reader function disabled.")

    def rungps(self):  # GPSモジュールを読み、GPSオブジェクトを更新する
        import serial
        s = None
        try:
            s = serial.Serial('/dev/serial0', 9600, timeout=10)
        except AttributeError:
            print(
                "[WARN] module serial has no Serial constructor. GPS funtion disabled.")
            return
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
                    self.lat = self.gps.latitude[0]
                    self.lon = self.gps.longitude[0]
                    self.alt = self.gps.altitude
                    self.course = self.gps.course
                    print('緯度:%2.8f, 経度:%2.8f, 海抜: %f, 方位: %f' %
                          (self.lat, self.lon, self.alt, self.course))
                    # print(f"利用衛星番号:{gps.satellites_used}")
                    # print('衛星番号: (仰角, 方位角, SN比)')
                    # print(gps.satellite_data)
                    # for k, v in deepcopy(gps.satellite_data.items()):
                    #     print('%d: %s' % (k, v))
                    # print('')
            except UnicodeDecodeError as e:
                pass
