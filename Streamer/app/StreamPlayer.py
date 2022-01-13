import pyaudio
from app.BytesStream import BytesStream
from threading import Thread


class StreamPlayer(Thread):
    """指定したストリームをframesずつ読み込み再生する"""
    daemon = True
    name = "StreamPlayer"

    def __init__(self, stream: BytesStream, rate: int, frames: int):
        Thread.__init__(self)
        self.stream = stream
        self.rate = rate
        self.frames = frames

    def run(self):
        # オーディオ出力ストリーム生成
        audio = pyaudio.PyAudio()

        # pyaudioのフレーム数には、ビット数の半分を指定する
        out_stream = audio.open(format=self.stream.format_bit//2,
                                channels=self.stream.channel,
                                rate=self.rate,
                                output=True,
                                frames_per_buffer=self.frames)
        while True:
            data = self.stream.readBytes(self.frames)
            out_stream.write(data)
