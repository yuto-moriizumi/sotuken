import wave
from app import BytesStream


class WaveStream(BytesStream.BytesStream):
    def __init__(self, filename: str, loop=False):
        self.file: wave.Wave_read = wave.open(filename, 'rb')
        self.loop = loop

    def read(self, frames: int):
        while True:
            data = self.file.readframes(frames)
            if self.loop and data == b'':
                self.file.rewind()
                continue
            break
        return self.file.readframes(frames)
