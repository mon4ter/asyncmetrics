from asyncio import StreamWriter
from typing import Iterable, Tuple

from .protocolerror import ProtocolError

__all__ = [
    'Protocol',
]


class Protocol:
    def __init__(self, host: str = '127.0.0.1', port: int = 2003):
        self._host = host
        self._port = port
        self._writer = None

    async def send(self, dataset: Iterable[Tuple[str, int, int]]):
        try:
            if not self._writer:
                self._writer = await self._connect()

            data = self._encode(dataset)
            await self._write(data)
        except Exception as exc:
            self.close()
            raise ProtocolError(*exc.args) from exc

    def close(self):
        if self._writer:
            self._writer.close()
            self._writer = None

    async def _connect(self) -> StreamWriter:
        raise NotImplementedError

    async def _write(self, data: bytes):
        self._writer.write(data)

    def _encode(self, dataset: Iterable[Tuple[str, int, int]]) -> bytes:
        raise NotImplementedError
