import numpy as np
from app.BytesStream import BytesStream
import pyaudio


class MicStream(BytesStream):
    def __init__(self, stream: pyaudio.Stream, format_bit: int, channel: int):
        self._stream = stream
        self.channel = channel
        self.format_bit = format_bit

    def readBytes(self, frames):
        # return self._stream.read(frames)
        return self._stream.read(frames, exception_on_overflow=False)
