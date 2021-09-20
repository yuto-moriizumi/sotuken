from app.StreamReader import StreamReader
from app.BytesStream import BytesStream
from app.AudioPropery import AudioProperty
from .GPS import GPS
import numpy as np
import socket
from threading import Thread


class SoundSendingClient(Thread):
    def __init__(self, server_host, server_port, gps: GPS, stream_reader: StreamReader, audio_property: AudioProperty):
        Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.gps = gps
        self.daemon = True
        self.name = "SoundSendingClient"
        self.stream_reader = stream_reader
        self.audio_property = audio_property
        self.last_count = -1
        self.retry_soon = False

    def run(self):
        DUMMY_FORMAT_BIT = 64
        DUMMY_NUMBER_COUNT = 3  # 何個の数字をダミーとして送るか

        # サーバに接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.SERVER_HOST, self.SERVER_PORT))
                # サーバにオーディオプロパティを送信
                audio_property_data = "{},{},{},{},{},{}".format(
                    self.audio_property.channel, self.audio_property.format_bit, self.audio_property.rate, self.audio_property.frames, DUMMY_FORMAT_BIT, DUMMY_NUMBER_COUNT).encode('utf-8')
                print(f"send:{audio_property_data}")
                sock.send(audio_property_data)

                self.stream_reader.sockets.append(sock)

                # メインループ

                while True:
                    continue
                    # data = self.stream.readNdarray(self.audio_property.frames)
                    last_count = self.stream_reader.count  # 別ｽﾚｯﾄﾞで更新されるので一旦ローカルに保存
                    if last_count == self.last_count:  # 新しいフレームセットが読み込まれていなければ何も送らない
                        continue
                    self.last_count = last_count
                    data = self.stream_reader.last_arr
                    # サーバに音データを送信
                    dummy = np.array(
                        [self.gps.lat, self.gps.lon, self.gps.alt], np.float64)
                    data_bytes = dummy.tobytes()+data.tobytes()
                    # print(
                    #     f"send:{len(data_bytes)} bytes {dummy} {data}")
                    # sock.send(data_bytes)
            except TimeoutError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was timeout.")
            except ConnectionResetError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was reseted.")
                self.retry_soon = True
            except ConnectionRefusedError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was refused.")
            except ConnectionAbortedError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} aborted.")
            except OSError as e:
                if e.errno == 113:
                    print(
                        f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was timeout.")
                else:
                    print(e.strerror)
