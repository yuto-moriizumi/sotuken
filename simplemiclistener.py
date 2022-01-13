from threading import Thread
import pyaudio

import numpy as np
import pyaudio

from abc import ABCMeta, abstractmethod

import numpy as np


class BytesStream(metaclass=ABCMeta):
    channel: int  # 1:モノクロ 2:ステレオ
    format_bit: int
    volume = 1

    @property
    def bytes_per_frame(self):
        return self.channel * self.format_bit

    @property
    def dtype(self):
        return np.dtype('>i' + str(self.format_bit//8)).type

    @abstractmethod
    def readBytes(self, frames: int) -> bytes:
        pass

    def readNdarray(self, frames: int) -> np.ndarray:
        return np.frombuffer(self.readBytes(frames), self.dtype)*self.volume


class MicStream(BytesStream):
    def __init__(self, stream: pyaudio.Stream, format_bit: int, channel: int):
        self._stream = stream
        self.channel = channel
        self.format_bit = format_bit

    def readBytes(self, frames):
        # return self._stream.read(frames)
        return self._stream.read(frames, exception_on_overflow=False)


class MicStreamBuilder():
    DEFAULT_CHANNEL = 2

    def build(self, format_bit: int, rate: int, frames: int):
        """マイクの入力ストリーム生成し返却します。
        デバイスを0番から順番に探し、名前によって利用できるマイクか判定します。
        予定出力チャンネルでのストリーム開設を目指すが、失敗したらチャンネル数を1減らします。"""
        print("Creating mic stream...")
        audio = pyaudio.PyAudio()
        mic_stream = None
        for channel in range(self.DEFAULT_CHANNEL, 0, -1):
            for i in range(audio.get_device_count()):
                try:
                    device_info = audio.get_device_info_by_index(i)
                    device_name: str = device_info["name"]
                    if "USB" in device_name:  # 名前に USB を含むデバイスならストリームを作成
                        # pyaudioのformatにはビット数の半分を指定する
                        stream = audio.open(format=format_bit//2,
                                            channels=channel,
                                            rate=rate,
                                            input=True,
                                            input_device_index=i, frames_per_buffer=frames)
                        mic_stream = MicStream(stream, format_bit, channel)
                        print(
                            f"Mic stream created with {device_info}")
                        break
                except OSError:  # 希望したチャンネル数にデバイスが対応していないなど
                    pass
        if mic_stream == None:
            print("[WARN] Creating mic stream failed")
        return mic_stream


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


class AudioProperty():
    def __init__(self, channel: int, format_bit: int,  rate: int, frames: int):
        self.channel = channel
        # サンプル幅 8bitなら8, 16bitなら16
        # pyAudioのフォーマット指定部には、なぜかビット数/2を指定する
        self.format_bit = format_bit
        self.rate = rate
        self.frames = frames  # 1度の送信で何フレーム送信するか


property = AudioProperty(1, 16,  44100, 8192)
mic_stream = MicStreamBuilder().build(
    property.format_bit, property.rate, property.frames)
player = StreamPlayer(mic_stream, property.rate, property.frames)
player.start()
while True:
    pass
