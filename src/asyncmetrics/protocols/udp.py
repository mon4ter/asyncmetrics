from asyncio import DatagramProtocol, StreamWriter, get_event_loop

from .protocol import Protocol


# noinspection PyAbstractClass
class Udp(Protocol):
    async def _connect(self) -> StreamWriter:
        writer, _ = await get_event_loop().create_datagram_endpoint(
            protocol_factory=DatagramProtocol,
            remote_addr=(self._host, self._port),
        )
        # noinspection PyUnresolvedReferences
        writer.write = writer.sendto
        # noinspection PyTypeChecker
        return writer
