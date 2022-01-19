# wav, マイク, (gps:未実装)の配信クライアント
# wavファイルのみの配信と、wav+マイクの配信に対応

import logging
from subprocess import TimeoutExpired
from .Magnetic import Magnetic
from .GPS import GPS
import math
import numpy as np
import pyaudio
import socket
from threading import Thread
import pyproj

DUMMY_BYTE_TYPE = np.float64


class SoundListeningServer(Thread):

    def __init__(self, server_host, server_port, gps: GPS, magnetic: Magnetic, disable_hit_judge=False):
        Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.gps = gps
        self.magnetic = magnetic
        self.daemon = True
        self.name = "SoundListeningServer"
        self.disable_hit_judge = disable_hit_judge
        self.last_message = "No incoming connection"
        self.socks: set[socket.socket] = set()
        self.recieves = dict()  # key:str "IPアドレス:ポート" value: lat, lonのタプル

    def getSocketList(self):
        return [':'.join([str(i) for i in s.getpeername()]) for s in self.socks]

    def run(self):
        # サーバーソケット生成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.SERVER_HOST, self.SERVER_PORT))
            server_sock.listen(16)
            logger = logging.getLogger(__name__)
            last_message = f"Listen Server listening on {self.SERVER_HOST}:{self.SERVER_PORT}"
            logger.info(last_message)
            self.last_message = last_message

            # クライアントと接続
            while True:
                client_sock, addr = server_sock.accept()
                hbuf, sbuf = socket.getnameinfo(
                    addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
                client_sock.settimeout(5)  # 5秒でタイムアウト
                msg = "accept:{}:{}".format(hbuf, sbuf)
                logger.info(msg)
                self.last_message = msg
                t = Thread(target=self.recv, args=[
                           client_sock, hbuf, sbuf], daemon=True, name="recv")
                t.start()

    def recv(self, client_sock: socket.socket, ip: str, port: str):
        with client_sock:
            # 他スレッドから読まれることを考慮して、最初にrevieves辞書を更新しておく
            client_addr = ':'.join([str(i)
                                    for i in client_sock.getpeername()])
            self.recieves[client_addr] = {
                "lat": -2, "lon": -2, "hit": False}
            self.socks.add(client_sock)
            logger = logging.getLogger(__name__)
            try:
                # クライアントからオーディオプロパティを受信
                settings_list = client_sock.recv(
                    256).decode('utf-8').split(",")
                CHANNEL = int(settings_list[0])
                FORMAT_BIT = int(settings_list[1])
                RATE = int(settings_list[2])
                FRAMES = int(settings_list[3])
                DUMMY_FORMAT_BIT = int(settings_list[4])
                DUMMY_NUMBER_COUNT = int(settings_list[5])
                frame_length = CHANNEL * FORMAT_BIT // 8 * \
                    FRAMES  # フレームの長さ(バイト)
                dummy_length = DUMMY_FORMAT_BIT // 8 * \
                    DUMMY_NUMBER_COUNT  # ダミーデータの長さ(バイト)
                data_length = frame_length + dummy_length

                # オーディオ出力ストリーム生成
                audio = pyaudio.PyAudio()

                # pyaudioのフレーム数には、ビット数の半分を指定する
                stream = audio.open(format=FORMAT_BIT//2,
                                    channels=CHANNEL,
                                    rate=RATE,
                                    output=True,
                                    frames_per_buffer=FRAMES)
                logger.info(settings_list)

                # メインループ
                data = bytes()
                EPSG4612 = pyproj.Proj("EPSG:4612")
                EPSG2451 = pyproj.Proj("EPSG:2451")
                while True:
                    # クライアントから音データを受信
                    data += (client_sock.recv(data_length))

                    # 切断処理
                    if not data:
                        self.socks.remove(client_sock)
                        break
                    if len(data) < data_length:  # データが必要量に達していなければなにもしない
                        continue
                    chunk = data[:data_length]  # 使用チャンク分だけ取り出す
                    data = data[data_length:]  # 今回使わないデータだけ残す
                    dummy_bytes = chunk[0:dummy_length]
                    sound = chunk[dummy_length:]
                    dummy_arr = np.frombuffer(dummy_bytes, np.float64)
                    sound_arr = np.frombuffer(sound, np.int16)
                    logger.info(
                        f"recv:{len(chunk)} bytes, dummy:{dummy_arr}, sound:{sound_arr}")
                    # print(np.frombuffer(chunk, np.int16)[:8])

                    # 方向判定
                    HIT_ANGLE = 45  # 中心から±何度までの誤差を許容するか
                    HIT_RADIUS = 100  # m単位

                    target_lat = dummy_arr[0]
                    target_lon = dummy_arr[1]

                    target_x, target_y = pyproj.transform(
                        EPSG4612, EPSG2451, target_lon, target_lat, always_xy=True)
                    my_x, my_y = pyproj.transform(
                        EPSG4612, EPSG2451, self.gps.lon, self.gps.lat, always_xy=True)

                    my_corce = self.magnetic.course
                    is_hit = self.is_hit(3,
                                         my_x, my_y, target_x, target_y, self.course_convert(my_corce-HIT_ANGLE), self.course_convert(my_corce+HIT_ANGLE), HIT_RADIUS)
                    # self.recieves[client_addr] = {
                    #     "lat": target_lat, "lon": target_lon, "hit": is_hit, "dummy": dummy_arr, "sound": sound_arr}
                    self.recieves[client_addr] = {"d_b": len(
                        dummy_bytes), "s_b": len(sound), "t_b": len(chunk), "dummy": dummy_arr, "sound": sound_arr}
                    logger.info(
                        f"is hit? {is_hit}")
                    if self.disable_hit_judge or is_hit:  # ヒット判定無効化時は再生する
                        stream.write(sound)  # 再生
            except UnicodeDecodeError:
                self.socks.remove(client_sock)
                msg = f"DecodeError with {ip}:{port}, connection reset"
                logger.error(msg)
                self.last_message = msg
            except TimeoutError:
                self.socks.remove(client_sock)
                msg = f"Connection with {ip}:{port} was timeout"
                logger.error(msg)
                self.last_message = msg
            except ConnectionResetError:
                self.socks.remove(client_sock)
                msg = f"Connection with {ip}:{port} was reset by peer"
                logger.error(msg)
                self.last_message = msg
            except TimeoutExpired:
                self.socks.remove(client_sock)
                msg = f"Connection with {ip}:{port} was timeout"
                logger.error(msg)
                self.last_message = msg
            except OSError as e:
                self.socks.remove(client_sock)
                if e.errno == 113 or e.errno == None:
                    msg = f"Connection with {ip}:{port} was timeout"
                    logger.error(msg)
                    self.last_message = msg
                else:
                    msg = f"Unhandled Exception on SLS {e.errno}"
                    logger.exception(msg)
                    self.last_message = msg
            except Exception as e:
                self.socks.remove(client_sock)
                msg = f"Unhandled Exception on SLS {e}"
                logger.exception(msg)
                self.last_message = msg

    def course_convert(self, course: float):
        """NMEAのcouse(進行方向)を、真東0°、真北90°の角度に変換する"""
        return (course*-1+90+360) % 360

    def is_hit(self, course_ignore_radius: float, start_x: float, start_y: float, target_x: float, target_y: float, start_angle: float, end_angle: float, radius: float):
        """当たり判定関数。course_ignoreは、方角判定を無視してtrueを返す近接距離(m単位)"""
        d = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
        return d < course_ignore_radius or self.hit_sector(start_x, start_y, target_x, target_y, start_angle, end_angle, radius)

    def hit_sector(self, start_x: float, start_y: float, target_x: float, target_y: float, start_angle: float, end_angle: float, radius: float):
        """真東を0°、真北を90°とし、start座標からradius径のangle内にtargetが収まっているか判定"""
        if start_angle > end_angle:
            start_angle, end_angle = end_angle, start_angle
        dx = target_x - start_x  # X = longtitude 経度
        dy = target_y - start_y  # Y = latitude 緯度
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
