import logging
from app.GPS import GPS
import numpy as np
from app.BytesStream import BytesStream
from threading import Thread


class StreamReader(Thread):
    daemon = True
    name = "StreamReader"
    count = 0
    sockets = []

    def __init__(self, stream: BytesStream, gps: GPS, frames: int, rate: int, debug=False):
        Thread.__init__(self)
        self.stream = stream
        self.gps = gps
        self.frames = frames
        self.rate = rate
        self.debug = debug
        print(
            f"initialize {self.stream.channel} x {self.frames} = {self.stream.channel * self.frames}")
        self.last_arr = np.zeros(
            self.stream.channel * self.frames, dtype=self.stream.dtype)

    def run(self):
        logger = logging.getLogger(__name__)
        try:
            sockets_2_delete = set()
            while True:
                dummy = np.array(
                    [self.gps.lat, self.gps.lon, self.gps.alt], np.float64)
                dummy_bytes = dummy.tobytes()
                sound_bytes: bytes = None
                if self.debug:
                    self.last_arr = self.stream.readNdarray(self.frames)
                    print(
                        f"read:{len(self.last_arr)} bytes {dummy} {self.last_arr}")
                    # time.sleep(self.frames/self.rate)
                    sound_bytes = self.last_arr.tobytes()
                    data_bytes = dummy_bytes+sound_bytes
                else:
                    sound_bytes = self.stream.readBytes(self.frames)
                    data_bytes = dummy_bytes+sound_bytes
                self.count += 1
                msg = f"sound:{len(sound_bytes)},dummy:{len(dummy_bytes)},total:{len(data_bytes)} {dummy} {self.last_arr}"
                for sock, ssc in self.sockets:
                    try:
                        sock.send(data_bytes)
                        sock_addr = ':'.join([str(i)
                                              for i in sock.getpeername()])
                        logger.info("send:"+sock_addr + msg)
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
