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
        while True:
            dummy = np.array(
                [self.gps.lat, self.gps.lon, self.gps.alt], np.float64)
            if self.debug:
                self.last_arr = self.stream.readNdarray(self.frames)
                print(
                    f"read:{len(self.last_arr)} bytes {dummy} {self.last_arr}")
                # time.sleep(self.frames/self.rate)
                data_bytes = dummy.tobytes()+self.last_arr.tobytes()
            else:
                data_bytes = dummy.tobytes()+self.stream.readBytes(self.frames)
            self.count += 1
            msg = f"read:{len(self.last_arr)} bytes {dummy} {self.last_arr}"
            for sock, ssc in self.sockets:
                sock.send(data_bytes)
                logger.info("send:"+':'.join([str(i)
                            for i in sock.getpeername()]) + msg)
                ssc.last_message = msg
                ssc.host.updateMessage()
