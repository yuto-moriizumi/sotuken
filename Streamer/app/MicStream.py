from app.BytesStream import BytesStream
import pyaudio


class MicStream(BytesStream):
    def __init__(self, stream: pyaudio.Stream, channel: int, format_type: int):
        self._stream = stream
        self.channel = channel
        self.format_type = format_type

    def read(self, frames):
        return self._stream.read(frames)
