class AudioProperty():
    def __init__(self, channel: int, format_bit: int,  rate: int, frames: int):
        self.channel = channel
        # サンプル幅 8bitなら8, 16bitなら16
        # pyAudioのフォーマット指定部には、なぜかビット数/2を指定する
        self.format_bit = format_bit
        self.rate = rate
        self.frames = frames  # 1度の送信で何フレーム送信するか
