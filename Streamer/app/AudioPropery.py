class AudioProperty():
    def __init__(self, format_type, channels, rate, chunk):
        self.format_type = format_type
        self.channels = channels
        self.rate = rate
        self.chunk = chunk  # 1度の送信で音声情報を何バイト送るか (なぜか指定数値の4倍量が送られる)
        # → 512バイト/2バイト*8ビット→ 4倍量 になってると思われる
