from app.BytesStream import BytesStream
import numpy as np


class MixStream(BytesStream):
    def __init__(self, *streams: BytesStream):
        self.streams = streams
        # TODO set stream channel here

    def read(self, frames: int):
        stream1 = self.streams[0]
        stream2 = self.streams[1]

        volume1 = 0.5
        volume2 = 0.5

        # 音量チェック
        if volume1 + volume2 > 1.0:
            return None

        # TODO: streamの長さが1の場合はただ返すだけ

        # 出力チャンネル数の決定
        out_channels = max(stream1.channel, stream2.channel)

        # デコード
        decoded_data1: np.ndarray = np.frombuffer(
            stream1.read(frames), stream1.format_type).copy()
        # モノラルならステレオに変換
        if stream1.channel < out_channels:
            decoded_data1 = self.mono2stereo(decoded_data1, frames)
        # データサイズの不足分を0埋め
        decoded_data1.resize(out_channels * frames, refcheck=False)

        # デコード
        decoded_data2: np.ndarray = np.frombuffer(
            stream2.read(frames), stream2.format_type).copy()
        # モノラルならステレオに変換
        if stream2.channel < out_channels:
            decoded_data2 = self.mono2stereo(decoded_data2, frames)
        # データサイズの不足分を0埋め
        decoded_data2.resize(out_channels * frames, refcheck=False)

        data = (decoded_data1 * volume1 + decoded_data2 *
                volume2).astype(stream1.format_type)
        print(type(data))
        return data

    def mono2stereo(self, data: np.ndarray, frames: int):
        output_data = np.zeros((2, frames))
        output_data[0] = data
        output_data[1] = data
        output_data = np.reshape(
            output_data.T, (frames * 2))
        return output_data.astype(np.int16)
