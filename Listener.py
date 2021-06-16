import pyaudio
import socket
import threading
import numpy as np

# サウンドストリームを受け取り、再生する

DUMMY_BYTE_TYPE = np.float64


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
                print(
                    f"recv:{len(chunk)} bytes, dummy:{np.frombuffer(dummy, DUMMY_BYTE_TYPE)}")
                print(np.frombuffer(chunk, np.int16)[:8])
                stream.write(sound)  # 再生


if __name__ == '__main__':
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345)
    mss_server.start()
    mss_server.join()
