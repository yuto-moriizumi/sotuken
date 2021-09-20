from app.BytesStream import BytesStream
import numpy as np


class MixStream(BytesStream):
    def __init__(self, *streams: BytesStream):
        self.streams = streams
        self.channel = max([s.channel for s in streams])
        self.format_bit = max([s.format_bit for s in streams])

    def readNdarray(self, frames: int):
        stream1 = self.streams[0]
        stream2 = self.streams[1]

        volume1 = 0.5
        volume2 = 0.5
        volume = 1/len(self.streams)

        # TODO: streamの長さが1の場合はただ返すだけ
        if len(self.streams) == 1:
            return np.frombuffer(
                self.streams[0].readBytes(frames), self.streams[0].dtype)

        # デコード
        decoded_arr = []
        for stream in self.streams:
            decoded_data: np.ndarray = np.frombuffer(
                stream.readBytes(frames), stream.dtype)
            # モノラルならステレオに変換
            if stream1.channel < self.channel:
                decoded_data = self.mono2stereo(decoded_data, frames)
            # データサイズの不足分を0埋め
            decoded_data.resize(self.channel * frames, refcheck=False)
            decoded_arr.append(decoded_data)

        data = sum(
            [decoded_data*volume for decoded_data in decoded_arr]).astype(np.int16)

        return data

    def readBytes(self, frames: int):
        return self.readNdarray(frames).tobytes()

    def mono2stereo(self, data: np.ndarray, frames: int):
        output_data = np.zeros((2, frames))
        output_data[0] = data
        output_data[1] = data
        output_data = np.reshape(
            output_data.T, (frames * 2))
        return output_data.astype(np.int16)
