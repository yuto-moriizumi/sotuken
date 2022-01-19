import logging
from app.StreamReader import StreamReader
from app.BytesStream import BytesStream
from app.AudioPropery import AudioProperty
from .GPS import GPS
import numpy as np
import socket
from threading import Thread


class SoundSendingClient(Thread):
    def __init__(self, server_host, server_port, gps: GPS, stream_reader: StreamReader, audio_property: AudioProperty, host):
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
        self.last_message = ""
        self.host = host

    def run(self):
        DUMMY_FORMAT_BIT = 64
        DUMMY_NUMBER_COUNT = 3  # 何個の数字をダミーとして送るか
        logger = logging.getLogger(__name__)

        # サーバに接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.settimeout(10)
                sock.connect((self.SERVER_HOST, self.SERVER_PORT))
                # サーバにオーディオプロパティを送信
                audio_property_data = "{},{},{},{},{},{}".format(
                    self.audio_property.channel, self.audio_property.format_bit, self.audio_property.rate, self.audio_property.frames, DUMMY_FORMAT_BIT, DUMMY_NUMBER_COUNT).encode('utf-8')
                self.host.last_message = f"send:{audio_property_data}"
                # self.host.updateMessage()
                logger.info(
                    f"connection established with {self.SERVER_HOST}:{self.SERVER_PORT}")
                # print(f"send:{audio_property_data}")
                sock.send(audio_property_data)
                self.stream_reader.sockets.append((sock, self))

                # メインループ

                while (sock, self) in self.stream_reader.sockets:
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
                # msg = f"connection with {self.SERVER_HOST}:{self.SERVER_PORT} was end by unknown reason"
                # self.host.last_message = msg
                # logger.warn(msg)
            except TimeoutError:
                self.host.last_message = "timeout"
                logger.warn(
                    f"connection with {self.SERVER_HOST}:{self.SERVER_PORT} was timeout")
                # self.host.updateMessage()
            except ConnectionResetError:
                self.host.last_message = "reseted"
                logger.warn(
                    f"connection with {self.SERVER_HOST}:{self.SERVER_PORT} was reseted")
                # self.host.updateMessage()
                self.retry_soon = True
            except ConnectionRefusedError:
                self.host.last_message = "refused"
                logger.warn(
                    f"connection with {self.SERVER_HOST}:{self.SERVER_PORT} was refused")
                # self.host.updateMessage()
            except ConnectionAbortedError:
                self.host.last_message = "aborted"
                logger.warn(
                    f"connection with {self.SERVER_HOST}:{self.SERVER_PORT} was aborted")
                # self.host.updateMessage()
            except OSError as e:
                if e.errno == 113:
                    self.host.last_message = "timeout"
                    logger.warn(
                        f"connection with {self.SERVER_HOST}:{self.SERVER_PORT} was timeout")
                    # self.host.updateMessage()
                else:
                    self.host.last_message = e.strerror
                    logger.error(e.strerror)
                    # self.host.updateMessage()
