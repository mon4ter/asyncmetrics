from typing import Iterable, Tuple

from .protocol import Protocol

__all__ = [
    'Plain',
]


# noinspection PyAbstractClass
class Plain(Protocol):
    def _encode(self, dataset: Iterable[Tuple[str, int, int]]) -> bytes:
        return ''.join('{} {} {}\n'.format(*tpl) for tpl in dataset).encode('ascii')
