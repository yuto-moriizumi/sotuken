from abc import ABCMeta, abstractmethod


class BytesStream(metaclass=ABCMeta):
    @property
    def channnel(self) -> int:
        pass

    @property
    def format(self) -> int:
        pass

    @abstractmethod
    def read(self, frames: int) -> bytes:
        pass
