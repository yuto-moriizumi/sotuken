from abc import ABCMeta, abstractmethod, abstractproperty


class BytesStream(metaclass=ABCMeta):
    channel: int  # 1:モノクロ 2:ステレオ
    format_type: int

    @abstractmethod
    def read(self, frames: int) -> bytes:
        pass

    def bytes_per_frame(self):
        return self.channel * self.format_type
