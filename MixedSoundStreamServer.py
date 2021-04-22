import pyaudio
import socket
import threading
import numpy as np


class MixedSoundStreamServer(threading.Thread):
    def __init__(self, server_host, server_port):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)

    def run(self):
        audio = pyaudio.PyAudio()

        # サーバーソケット生成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.SERVER_HOST, self.SERVER_PORT))
            server_sock.listen(4)

            # クライアントと接続
            client_sock, addr = server_sock.accept()
            hbuf, sbuf = socket.getnameinfo(
                addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
            print("accept:{}:{}".format(hbuf, sbuf))
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
                stream = audio.open(format=FORMAT,
                                    channels=CHANNELS,
                                    rate=RATE,
                                    output=True,
                                    frames_per_buffer=CHUNK)

                print(settings_list)
                # メインループ
                while True:
                    # クライアントから音データを受信
                    # なぜかクライアントがCHUNKの4倍量を送ってくるので合わせる。
                    data = client_sock.recv(CHUNK*4+DUMMY_BYTES)

                    # 切断処理
                    if not data:
                        break

                    # print(
                    #     f"recv{np.frombuffer(data, np.int16)[0:DUMMY_BYTES//2]}")
                    dummy = data[0:DUMMY_BYTES]
                    print(
                        f"recv:{len(data)} bytes, dummy:{np.frombuffer(dummy, np.int16)}")
                    data = data[DUMMY_BYTES:]
                    print(np.frombuffer(data, np.int16)[:8])

                    # オーディオ出力ストリームにデータ書き込み
                    stream.write(data)

        # 終了処理
        stream.stop_stream()
        stream.close()

        audio.terminate()


if __name__ == '__main__':
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345)
    mss_server.start()
    mss_server.join()
