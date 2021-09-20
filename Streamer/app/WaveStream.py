import wave

import pyaudio
from app import BytesStream


class WaveStream(BytesStream.BytesStream):
    def __init__(self, filename: str, format_bit: int, loop=False):
        self.file: wave.Wave_read = wave.open(filename, 'rb')
        self.loop = loop
        self.channel = self.file.getnchannels()
        self.format_bit = format_bit

    def readBytes(self, frames: int):
        while True:
            data = self.file.readframes(frames)
            if self.loop and data == b'':
                self.file.rewind()
                continue
            break
        return data
