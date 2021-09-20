import socket
from app.GPS import GPS
import time
import numpy as np
from app.BytesStream import BytesStream
from threading import Thread


class StreamReader(Thread):
    daemon = True
    name = "StreamReader"
    count = 0
    sockets: list[socket.socket] = []

    def __init__(self, stream: BytesStream, gps: GPS, frames: int, rate: int):
        Thread.__init__(self)
        self.stream = stream
        self.gps = gps
        self.frames = frames
        self.rate = rate
        print(
            f"initialisxe {self.stream.channel} x {self.frames} = {self.stream.channel * self.frames}")
        self.last_arr = np.zeros(
            self.stream.channel * self.frames, dtype=self.stream.dtype)

    def run(self):
        while True:
            self.last_arr = self.stream.readNdarray(self.frames)
            dummy = np.array(
                [self.gps.lat, self.gps.lon, self.gps.alt], np.float64)
            print(
                f"read:{len(self.last_arr)} bytes {dummy} {self.last_arr}")
            # time.sleep(self.frames/self.rate)
            self.count += 1
            data_bytes = dummy.tobytes()+self.last_arr.tobytes()
            for sock in self.sockets:
                sock.send(data_bytes)
