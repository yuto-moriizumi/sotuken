# wav, マイク, (gps:未実装)の配信クライアント
# wavファイルのみの配信と、wav+マイクの配信に対応

import matplotlib.pyplot as plt
import logging
from subprocess import TimeoutExpired
import math
import numpy as np
import socket
from threading import Thread

from ENV import DISABLE_HIT_JUDGE, MAX_HOST, DEBUG as DEBUG_MODE, DEVICE_TYPE, NETWORK_ADDRESS, HOST_ADDRESS_START, MAX_X, MIN_X, MAX_Y, MIN_Y

DUMMY_BYTE_TYPE = np.float64


def getMyIp():
    host_addr = ""
    for i in range(HOST_ADDRESS_START, HOST_ADDRESS_START+MAX_HOST):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((NETWORK_ADDRESS+str(i), 12345))
                sock.listen(5)
                host_addr = NETWORK_ADDRESS+str(i)
                sock.close()
            break
        except Exception:
            continue
    return host_addr


class MasterServer(Thread):

    def __init__(self, server_host, server_port):
        Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.daemon = True
        self.name = "MasterServer"
        self.last_message = "No incoming connection"
        self.socks: set[socket.socket] = set()
        self.recieves = dict()  # key:str "IPアドレス:ポート" value: lat, lonのタプル

    def getSocketList(self):
        return [':'.join([str(i) for i in s.getpeername()]) for s in self.socks]

    def run(self):
        # サーバーソケット生成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.SERVER_HOST, self.SERVER_PORT))
            server_sock.settimeout(5)
            server_sock.listen(16)
            print(
                f"Listen Server listening on {self.SERVER_HOST}:{self.SERVER_PORT}")
            # クライアントと接続
            while True:
                client_sock, addr = server_sock.accept()
                hbuf, sbuf = socket.getnameinfo(
                    addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
                client_sock.settimeout(5)  # 5秒でタイムアウト
                print(f"accept:{hbuf}:{sbuf}")
                t = Thread(target=self.recv, args=[
                           client_sock, hbuf, sbuf], daemon=True, name="recv")
                t.start()

    def recv(self, client_sock: socket.socket, ip: str, port: str):
        with client_sock:
            # 他スレッドから読まれることを考慮して、最初にrevieves辞書を更新しておく
            client_addr = ':'.join([str(i)
                                    for i in client_sock.getpeername()])
            self.recieves[client_addr] = {
                "lat": -2, "lon": -2, "course": 90}
            self.socks.add(client_sock)
            try:
                # クライアントからオーディオプロパティを受信
                settings_list = client_sock.recv(
                    256).decode('utf-8').split(",")
                CHANNEL = int(settings_list[0])
                FORMAT_BIT = int(settings_list[1])
                # RATE = int(settings_list[2])
                FRAMES = int(settings_list[3])
                DUMMY_FORMAT_BIT = int(settings_list[4])
                DUMMY_NUMBER_COUNT = int(settings_list[5])
                frame_length = CHANNEL * FORMAT_BIT // 8 * \
                    FRAMES  # フレームの長さ(バイト)
                dummy_length = DUMMY_FORMAT_BIT // 8 * \
                    DUMMY_NUMBER_COUNT  # ダミーデータの長さ(バイト)
                data_length = frame_length + dummy_length

                print(settings_list)

                # メインループ
                data = bytes()

                while True:
                    # クライアントから音データを受信
                    # なぜかクライアントがCHUNKの4倍量を送ってくるので合わせる。

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
                    dummy_arr = np.frombuffer(dummy_bytes, np.float64)
                    lat, lon, course = dummy_arr

                    self.recieves[client_addr] = {
                        "lat": lat, "lon": lon, "course": course}
                    print(client_addr, self.recieves[client_addr])

            except UnicodeDecodeError:
                self.socks.remove(client_sock)
                msg = f"DecodeError with {ip}:{port}, connection reset"
                print(msg)
                self.last_message = msg
            except TimeoutError:
                self.socks.remove(client_sock)
                msg = f"Connection with {ip}:{port} was timeout1"
                print(msg)
                self.last_message = msg
            except ConnectionResetError:
                self.socks.remove(client_sock)
                msg = f"Connection with {ip}:{port} was reset by peer"
                print(msg)
                self.last_message = msg
            except TimeoutExpired:
                self.socks.remove(client_sock)
                msg = f"Connection with {ip}:{port} was timeout2"
                print(msg)
                self.last_message = msg
            except OSError as e:
                self.socks.remove(client_sock)
                if e.errno == 113 or e.errno == None:
                    msg = f"Connection with {ip}:{port} was timeout3"
                    print(msg)
                    self.last_message = msg
                else:
                    msg = f"Unhandled Exception on SLS {e.errno}"
                    print(msg)
                    self.last_message = msg
            except Exception as e:
                self.socks.remove(client_sock)
                msg = f"Unhandled Exception on SLS {e}"
                print(msg)
                self.last_message = msg

    def course_convert(self, course: float):
        """NMEAのcouse(進行方向)を、真東0°、真北90°の角度に変換する"""
        return (course*-1+90+360) % 360

    def hit_sector(self, target_x: float, target_y: float, start_angle: float, end_angle: float, radius: float):
        """真東を0°、真北を90°とする"""
        if start_angle > end_angle:
            start_angle, end_angle = end_angle, start_angle
        dx = target_x - self.gps.lon  # X = longtitude 経度
        dy = target_y - self.gps.lat  # Y = latitude 緯度
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


def main():
    try:
        # host_addr = getMyIp()
        host_addr = "192.168.86.21"
        ms = MasterServer(host_addr, 12345)
        ms.start()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        import pyproj

        EPSG4612 = pyproj.Proj("EPSG:4612")
        EPSG2451 = pyproj.Proj("EPSG:2451")

        while True:
            # ax.set_xlim([135, 145])
            # ax.set_ylim([32.5, 37.5])
            sockets = ms.getSocketList()
            annotates = []
            for socket in sockets:
                lat = ms.recieves[socket]["lat"]
                lon = ms.recieves[socket]["lon"]
                course = ms.recieves[socket]["course"]
                rad = math.radians(ms.course_convert(course))
                x, y = pyproj.transform(
                    EPSG4612, EPSG2451, lon, lat, always_xy=True)
                target_y = lat + math.sin(rad)
                target_x = lon + math.cos(rad)
                host_addr = socket.split(":")[0].split(".")[-1]
                # ap = ax.plot(x, y, 'o', color="red", label=host_addr)
                ax.scatter(x, y, marker='o', label=host_addr)
                print(x, y)
                # ap = ax.plot(lon, lat, 'o', color="red", label=host_addr)
                # an = ax.annotate(host_addr, xy=(target_x, target_y), xytext=(lon, lat),
                #                  arrowprops=dict(shrink=0, width=1, headwidth=8,
                #                                  headlength=10, connectionstyle='arc3',
                #                                  facecolor='gray', edgecolor='gray')
                #                  )
                # an = ax.arrow(lon, lat, target_x-lon, target_y-lat, width=0.1)
                an = ax.arrow(x, y, 2*math.cos(rad), 2 * math.sin(rad))
                # annotates.append(an)
            ax.set_xlim(auto=True)
            ax.set_ylim(auto=True)
            ax.legend()
            plt.pause(1)
            for annnotate in annotates:
                annnotate.remove()
            annotates.clear()
            ax.clear()
            continue
    except KeyboardInterrupt:
        print("Exit.")
        exit(0)


if __name__ == '__main__':
    main()
