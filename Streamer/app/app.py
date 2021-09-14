# wav, マイク, (gps:未実装)の配信クライアント
# wavファイルのみの配信と、wav+マイクの配信に対応

from .GPS import GPS
import math
import numpy as np
import pyaudio
import socket
import threading


DUMMY_BYTE_TYPE = np.float64


class MixedSoundStreamServer(threading.Thread):

    def __init__(self, server_host, server_port, gps: GPS):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.gps = gps

    def run(self):
        print("Sound Stream Listener started")
        # サーバーソケット生成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.SERVER_HOST, self.SERVER_PORT))
            server_sock.listen(4)

            # クライアントと接続
            while True:
                client_sock, addr = server_sock.accept()
                hbuf, sbuf = socket.getnameinfo(
                    addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
                print("accept:{}:{}".format(hbuf, sbuf))
                t = threading.Thread(target=self.recv, args=[client_sock])
                t.start()

    def recv(self, client_sock):
        with client_sock:
            # クライアントからオーディオプロパティを受信
            settings_list = client_sock.recv(
                256).decode('utf-8').split(",")
            FORMAT = int(settings_list[0])
            CHANNELS = int(settings_list[1])
            RATE = int(settings_list[2])
            CHUNK = int(settings_list[3])
            DUMMY_BYTES = int(settings_list[4])

            # オーディオ出力ストリーム生成
            audio = pyaudio.PyAudio()
            stream = audio.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                output=True,
                                frames_per_buffer=CHUNK)

            print(settings_list)

            # メインループ
            data = b""
            while True:
                # クライアントから音データを受信
                # なぜかクライアントがCHUNKの4倍量を送ってくるので合わせる。
                data += (client_sock.recv(CHUNK*4+DUMMY_BYTES))

                # 切断処理
                if not data:
                    break
                if len(data) < CHUNK*4+DUMMY_BYTES:  # データが必要量に達していなければなにもしない
                    continue
                chunk = data[:CHUNK*4+DUMMY_BYTES]  # 使用チャンク分だけ取り出す
                data = data[CHUNK*4+DUMMY_BYTES:]  # 今回使わないデータだけ残す
                dummy = chunk[0:DUMMY_BYTES]
                sound = chunk[DUMMY_BYTES:]
                # print(
                #     f"recv:{len(chunk)} bytes, dummy:{np.frombuffer(dummy, DUMMY_BYTE_TYPE)}")
                # print(np.frombuffer(chunk, np.int16)[:8])

                # 方向判定
                HIT_ANGLE = 45  # 中心から±何度までの誤差を許容するか
                HIT_RADIUS = 10
                target_lat = dummy[0]
                target_lon = dummy[0]
                my_corce = self.gps.course
                is_hit = self.hit_sector(
                    target_lon, target_lat, my_corce-HIT_ANGLE, my_corce+HIT_ANGLE, HIT_RADIUS)
                # print(
                #    f"is hit? {is_hit}")
                if is_hit:
                    stream.write(sound)  # 再生

    def hit_sector(self, target_x, target_y, start_angle, end_angle, radius):
        dx = target_x - self.gps.lon
        dy = target_y - self.gps.lat
        sx = math.cos(math.radians(start_angle))
        sy = math.sin(math.radians(start_angle))
        ex = math.cos(math.radians(end_angle))
        ey = math.sin(math.radians(end_angle))

        # 円の内外判定
        if dx ** 2 + dy ** 2 > radius ** 2:
            return False

        # 扇型の角度が180を超えているか
        if sx * ey - ex * sy > 0:
            # 開始角に対して左にあるか
            if sx * dy - dx * sy < 0:
                return False
            # 終了角に対して右にあるか
            if ex * dy - dx * ey > 0:
                return False
            # 扇型の内部にあることがわかった
            return True
        else:
            # 開始角に対して左にあるか
            if sx * dy - dx * sy >= 0:
                return True
            # 終了角に対して右にあるか
            if ex * dy - dx * ey <= 0:
                return True
            # 扇型の外部にあることがわかった
            return False
