from app.BytesStream import BytesStream
import pyaudio


class MicStream(BytesStream):
    def __init__(self, stream: pyaudio.Stream, channel: int):
        self._stream = stream
        self.channel = channel

    def read(self, frames):
        return self._stream.read(frames)
