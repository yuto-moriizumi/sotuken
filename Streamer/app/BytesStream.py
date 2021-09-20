from abc import ABCMeta, abstractmethod, abstractproperty

import numpy as np


class BytesStream(metaclass=ABCMeta):
    channel: int  # 1:モノクロ 2:ステレオ
    format_bit: int

    @abstractmethod
    def read(self, frames: int) -> bytes:
        pass

    def bytes_per_frame(self):
        return self.channel * self.format_bit

    @property
    def dtype(self):
        return np.dtype('>i' + str(self.format_bit//2))
