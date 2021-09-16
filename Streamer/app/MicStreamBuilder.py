from app.MicStream import MicStream
import pyaudio


class MicStreamBuilder():
    DEFAULT_CHANNEL = 2

    def build(self, format_type: int, rate: int, frames_per_buffer: int):
        """マイクの入力ストリーム生成し返却します。
        デバイスを0番から順番に探し、名前によって利用できるマイクか判定します。
        予定出力チャンネルでのストリーム開設を目指すが、失敗したらチャンネル数を1減らします。"""
        print("Creating mic stream...")
        audio = pyaudio.PyAudio()
        mic_stream = None
        for channels in range(self.DEFAULT_CHANNEL, 0, -1):
            for i in range(audio.get_device_count()):
                try:
                    device_info = audio.get_device_info_by_index(i)
                    device_name: str = device_info["name"]
                    if "USB" in device_name:  # 名前に USB を含むデバイスならストリームを作成
                        stream = audio.open(format=format_type,
                                            channels=channels,
                                            rate=rate,
                                            input=True,
                                            frames_per_buffer=frames_per_buffer, input_device_index=i)
                        mic_stream = MicStream(stream, channels, format_type)
                        print(
                            f"Mic stream created with {device_info}")
                        break
                except OSError:  # 希望したチャンネル数にデバイスが対応していないなど
                    pass
        if mic_stream == None:
            print("[WARN] Creating mic stream failed")
        return mic_stream
