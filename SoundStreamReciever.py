import socket
import threading
import numpy as np


class MixedSoundStreamServer(threading.Thread):
    def __init__(self, server_host, server_port):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)

    def run(self):

        # サーバーソケット生成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.SERVER_HOST, self.SERVER_PORT))
            server_sock.listen(1)

            # クライアントと接続
            client_sock, _ = server_sock.accept()
            with client_sock:
                # クライアントからオーディオプロパティを受信
                settings_list = client_sock.recv(
                    256).decode('utf-8').split(",")
                CHUNK = int(settings_list[3])
                DUMMY_BYTES = int(settings_list[4])

                print(settings_list)
                # メインループ
                db_left = 0  # dummy bytes start at
                # 16bitなので数字1つにつき2バイト 2バイトで割った数がダミーの数字の個数
                dummies = [-1]*(DUMMY_BYTES//2)

                while True:
                    # クライアントから音データを受信
                    # なぜかクライアントがCHUNKの4倍量を送ってくるので合わせる。
                    data = client_sock.recv(CHUNK*4+DUMMY_BYTES)

                    # 切断処理
                    if not data:
                        break

                    # print(
                    #     f"recv{np.frombuffer(data, np.int16)[0:DUMMY_BYTES//2]}")

                    db_right = db_left+DUMMY_BYTES
                    dbl2r = min(max(db_left, 0), len(data))
                    dbr2r = min(max(db_right, 0), len(data))
                    didx = dbl2r-db_left  # 本来のインデックス位置とのズレ

                    t_dummies = data[dbl2r:dbr2r]
                    for i in range(len(t_dummies)):
                        dummies[i+didx] = t_dummies[i]

                    print(
                        f"recv:{len(data)} bytes, t_d:{np.frombuffer(t_dummies, np.int16)}, d:{np.frombuffer(dummies, np.int16)}")
                    s_data = data[:dbl2r].extend(data[dbr2r:])
                    print(np.frombuffer(data, np.int16)[:8])
                    print(
                        f"dbl:{db_left} dbl2r:{dbl2r} dbr:{db_right} dbr2r:{dbr2r} didx:{didx}")
                    db_left = (db_left+len(data)) % (CHUNK*4+DUMMY_BYTES)


if __name__ == '__main__':
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345)
    mss_server.start()
    mss_server.join()
