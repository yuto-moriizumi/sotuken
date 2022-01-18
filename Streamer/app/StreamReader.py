import logging
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

    def __init__(self, stream: BytesStream, gps: GPS, audio_property: AudioProperty, debug=False):
        Thread.__init__(self)
        self.stream = stream
        self.gps = gps
        self.debug = debug
        self.audio_property = audio_property
        print(
            f"initialize {self.stream.channel} x {self.audio_property.frames} = {self.stream.channel * self.audio_property.frames}")

    def run(self):
        logger = logging.getLogger(__name__)
        try:
            sockets_2_delete = set()
            raw_sound_bytes = bytes()
            while True:
                dummy_arr = np.array(
                    [self.gps.lat, self.gps.lon, self.gps.alt], np.float64)
                dummy_bytes = dummy_arr.tobytes()
                if True or self.debug:
                    sound_arr = self.stream.readNdarray(
                        self.audio_property.frames)
                    raw_sound_bytes += sound_arr.tobytes()
                else:
                    sound_bytes += self.stream.readBytes(
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
                for sock, ssc in self.sockets:
                    try:
                        sock.send(data_bytes)
                        sock_addr = ':'.join([str(i)
                                              for i in sock.getpeername()])
                        msg = "send:"+sock_addr + \
                            f" sound:{len(sound_bytes)},dummy:{len(dummy_bytes)},total:{len(data_bytes)} {dummy_arr} {sound_arr}"
                        logger.info(msg)
                    except Exception:
                        logger.error(
                            f"socket error occured on reader, removing {sock_addr}")
                        sockets_2_delete.add(sock)
                    ssc.host.last_message = msg
                for sock in sockets_2_delete:
                    self.sockets.remove(sock)
        except Exception:
            msg = "Unhandled Exception Occured"
            print(msg)
            logger.exception(msg)
