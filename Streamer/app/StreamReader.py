import time
import numpy as np
from app.BytesStream import BytesStream
from threading import Thread


class StreamReader(Thread):
    daemon = True
    name = "StreamReader"
    count = 0

    def __init__(self, stream: BytesStream, frames: int, rate: int):
        Thread.__init__(self)
        self.stream = stream
        self.frames = frames
        self.rate = rate
        print(
            f"initialisxe {self.stream.channel} x {self.frames} = {self.stream.channel * self.frames}")
        self.last_arr = np.zeros(
            self.stream.channel * self.frames, dtype=self.stream.dtype)

    def run(self):
        while True:
            self.last_arr = self.stream.readNdarray(self.frames)
            print(f"read: {self.last_arr}")
            # time.sleep(self.frames/self.rate)
            self.count += 1
