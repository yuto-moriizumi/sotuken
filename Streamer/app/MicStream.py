import pyaudio


class MicStream():
    DEFAULT_CHANNEL = 2
    channel: int = DEFAULT_CHANNEL
    stream: pyaudio.Stream = None

    def __init__(self, format: int, rate: int, frames_per_buffer: int):
        """マイクの入力ストリーム生成し返却します。
        デバイスを0番から順番に探し、名前によって利用できるマイクか判定します。
        予定出力チャンネルでのストリーム開設を目指すが、失敗したらチャンネル数を1減らします。"""
        audio = pyaudio.PyAudio()
        for channels in range(self.DEFAULT_CHANNEL, 0, -1):
            for i in range(audio.get_device_count()):
                try:
                    device_info = audio.get_device_info_by_index(i)
                    device_name: str = device_info["name"]
                    if "USB" in device_name:  # 名前に USB を含むデバイスならストリームを作成
                        self.stream = audio.open(format=format,
                                                 channels=channels,
                                                 rate=rate,
                                                 input=True,
                                                 frames_per_buffer=frames_per_buffer, input_device_index=i)
                        self.channel = channels
                        print(
                            f"mic stream created with {device_info}")
                        break
                except:
                    pass
        if self.stream == None:
            print("[WARN] creating mic_stream failed")
