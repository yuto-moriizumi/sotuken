from app.BytesStream import BytesStream
import pyaudio


class MicStream(BytesStream):
    def __init__(self, stream: pyaudio.Stream, format_bit: int, channel: int):
        self._stream = stream
        self.channel = channel
        self.format_bit = format_bit

    def read(self, frames):
        return self._stream.read(frames)
