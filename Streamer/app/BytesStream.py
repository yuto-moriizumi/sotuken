from abc import ABCMeta, abstractmethod, abstractproperty


class BytesStream(metaclass=ABCMeta):
    channel: int
    format_type: int

    @abstractmethod
    def read(self, frames: int) -> bytes:
        pass
