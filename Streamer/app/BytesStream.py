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
