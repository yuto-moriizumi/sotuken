from abc import ABCMeta, abstractmethod


class BytesStream(metaclass=ABCMeta):
    @abstractmethod
    def read(self, frames: int) -> bytes:
        pass
