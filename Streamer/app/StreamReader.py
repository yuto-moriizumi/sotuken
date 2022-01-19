import logging
import socket
from app.AudioPropery import AudioProperty
from app.GPS import GPS
import numpy as np
from app.BytesStream import BytesStream
from threading import Thread


class StreamReader(Thread):
    daemon = True
    name = "StreamReader"
    count = 0
    sockets = []

    def __init__(self, stream: BytesStream, gps: GPS, audio_property: AudioProperty, debug=False, magnetic=None):
        Thread.__init__(self)
        self.stream = stream
        self.gps = gps
        self.magnetic = magnetic
        self.debug = debug
        self.audio_property = audio_property
        print(
            f"initialize {self.stream.channel} x {self.audio_property.frames} = {self.stream.channel * self.audio_property.frames}")

    def run(self):
        logger = logging.getLogger(__name__)

        # HOST_NAME = '192.168.86.255'
        # PORT = 12345
        # # ipv4を使うので、AF_INET
        # # udp通信を使いたいので、SOCK_DGRAM
        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # # ブロードキャストを行うので、設定
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # # データ送信
        # sock.sendto(b"Hello, UDP BroadCast", (HOST_NAME, PORT))
        # sock.close()

        try:
            sockets_2_delete = set()
            raw_sound_bytes = bytes()

            HOST_NAME = '192.168.86.255'
            PORT = 12345
            # ipv4を使うので、AF_INET
            # udp通信を使いたいので、SOCK_DGRAM
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # ブロードキャストを行うので、設定
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # sock.close()

            while True:
                dummy_list = [self.gps.lat, self.gps.lon,
                              self.magnetic.course if self.magnetic != None else self.gps.alt]
                dummy_arr = np.array(dummy_list, np.float64)
                dummy_bytes = dummy_arr.tobytes()
                if True or self.debug:
                    sound_arr = self.stream.readNdarray(
                        self.audio_property.frames)
                    raw_sound_bytes += sound_arr.tobytes()
                else:
                    raw_sound_bytes += self.stream.readBytes(
                        self.audio_property.frames)

                default_sound_frame_length = self.audio_property.getFrameLength()
                # 音楽データ部が必要バイト数に未達であれば、送信をしない
                if len(raw_sound_bytes) < default_sound_frame_length:
                    continue
                # 今回送信するフレーム群のみ取り出す
                sound_bytes = raw_sound_bytes[:default_sound_frame_length]
                raw_sound_bytes = raw_sound_bytes[default_sound_frame_length:]
                data_bytes = dummy_bytes+sound_bytes
                self.count += 1
                # データ送信
                # print(f"send:{dummy_arr} {sound_arr}")
                sock.sendto(data_bytes, (HOST_NAME, PORT))
                # sock.sendto(data_bytes, (HOST_NAME, PORT))
        # for sock, ssc in self.sockets:
        #     try:
        #         sock.send(data_bytes)
        #         sock_addr = ':'.join([str(i)
        #                               for i in sock.getpeername()])
        #         msg = "send:"+sock_addr + \
        #             f" sound:{len(sound_bytes)},dummy:{len(dummy_bytes)},total:{len(data_bytes)} {dummy_arr} {sound_arr}"
        #         logger.info(msg)
        #     except TimeoutError:
        #         sockets_2_delete.add((sock, ssc))
        #         msg = "timeout"
        #         logger.warn(
        #             f"connection with {sock_addr} was timeout")
        #     except ConnectionResetError:
        #         sockets_2_delete.add((sock, ssc))
        #         msg = "reseted"
        #         logger.warn(
        #             f"connection with {sock_addr} was reseted")
        #         # self.retry_soon = True
        #     except ConnectionRefusedError:
        #         sockets_2_delete.add((sock, ssc))
        #         msg = "refused"
        #         logger.warn(
        #             f"connection with {sock_addr} was refused")
        #     except ConnectionAbortedError:
        #         sockets_2_delete.add((sock, ssc))
        #         msg = "aborted"
        #         logger.warn(
        #             f"connection with {sock_addr} was aborted")
        #     except OSError as e:
        #         sockets_2_delete.add((sock, ssc))
        #         if e.errno == 113:
        #             msg = "timeout"
        #             logger.warn(
        #                 f"connection with {sock_addr} was timeout")
        #         elif e.errno == 107:
        #             msg = "already disconnected by the another"
        #             logger.warn(
        #                 f"connection with {sock_addr} was already disconnected by the another")
        #         else:
        #             msg = sock_addr+" "+e.strerror
        #             logger.exception(msg)
        #     except Exception as e:
        #         msg = f"Unhandled exception occured {e}"
        #         logger.exception(msg)
        #         sockets_2_delete.add((sock, ssc))
        #     ssc.host.last_message = msg
        # for sockset in sockets_2_delete:
        #     self.sockets.remove(sockset)
        # sockets_2_delete.clear()
        except Exception:
            msg = "Unhandled Exception Occured"
            print(msg)
            logger.exception(msg)
