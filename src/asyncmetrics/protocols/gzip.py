from gzip import compress
from typing import Iterable, Tuple

from .plain import Plain

__all__ = [
    'Gzip',
]


# noinspection PyAbstractClass
class Gzip(Plain):
    def _encode(self, dataset: Iterable[Tuple[str, int, int]]) -> bytes:
        data = super()._encode(dataset)
        return compress(data)
