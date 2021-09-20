from app.BytesStream import BytesStream
from app.AudioPropery import AudioProperty
from .GPS import GPS
import numpy as np
import socket
from threading import Thread


class MixedSoundStreamClient(Thread):
    def __init__(self, server_host, server_port, gps: GPS, input_stream: BytesStream, audio_property: AudioProperty):
        Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.gps = gps
        self.daemon = True
        self.name = "MixedSoundStreamClient"
        self.stream = input_stream
        self.audio_property = audio_property

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
                # メインループ

                while True:
                    data = self.stream.read(self.audio_property.frames)
                    # サーバに音データを送信
                    dummy = np.array(
                        [self.gps.lat, self.gps.lon, self.gps.alt], np.float64)
                    data_bytes = dummy.tobytes()+data.tobytes()
                    print(f"send:{len(data_bytes)} bytes {dummy} {data}")
                    sock.send(data_bytes)
            except TimeoutError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was timeout.")
            except ConnectionResetError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was reseted.")
            except ConnectionRefusedError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was refused.")
            except ConnectionAbortedError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} aborted.")
