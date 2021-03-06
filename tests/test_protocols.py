from asyncio import DatagramProtocol, StreamReader, get_event_loop, sleep, start_server
from gzip import decompress
from random import randint
from typing import Tuple

from pytest import mark, raises

from asyncmetrics import GzipTcp, PlainTcp, PlainUdp, ProtocolError
from asyncmetrics.protocols.protocol import Protocol


class TcpServer:
    def __init__(self, sent: list):
        self._sent = sent
        self._server = None

    async def _cb(self, r: StreamReader, _w):
        self._sent.append(await r.readuntil())

    async def __aenter__(self) -> Tuple[str, int]:
        self._server = await start_server(client_connected_cb=self._cb, host='127.0.0.1', port=0)
        return self._server.sockets[0].getsockname()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._server.close()
        await self._server.wait_closed()


class SentDatagramProtocol(DatagramProtocol):
    def __init__(self, sent: list):
        self._sent = sent

    def __call__(self):
        return type(self)(self._sent)

    def datagram_received(self, data: bytes, addr):
        self._sent.append(data)


class UdpServer:
    def __init__(self, sent: list):
        self._sent = sent
        self._transport = None

    async def __aenter__(self) -> Tuple[str, int]:
        address = '127.0.0.1', randint(1024, 65535)
        self._transport, _ = await get_event_loop().create_datagram_endpoint(
            SentDatagramProtocol(self._sent),
            local_addr=address,
        )
        return address

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._transport.close()


@mark.parametrize('datatset,data', [
    (
        [('one', 1, 1)],
        b'one 1 1\n'
    ),
    (
        [('two', 2, 2), ('two', 3, 3)],
        b'two 2 2\ntwo 3 3\n'
    ),
])
def test_plain(datatset, data):
    assert PlainTcp()._encode(datatset) == data


@mark.asyncio
async def test_tcp():
    sent = []

    async with TcpServer(sent) as (host, port):
        writer = await PlainTcp(host, port)._connect()

        writer.write(b'test_tcp\n')
        await writer.drain()
        await sleep(.001)

        writer.close()

    assert sent == [b'test_tcp\n']


@mark.asyncio
async def test_protocol_connect_abc():
    with raises(NotImplementedError):
        await Protocol()._connect()


def test_protocol_encode_abc():
    with raises(NotImplementedError):
        Protocol()._encode([])


@mark.asyncio
async def test_send_tcp():
    sent = []

    async with TcpServer(sent) as (host, port):
        protocol = PlainTcp(host, port)
        await protocol.send([('test_send_tcp', 1, 1)])
        await sleep(.001)
        protocol.close()

    assert sent == [b'test_send_tcp 1 1\n']


@mark.asyncio
async def test_send_failed():
    async with TcpServer([]) as (host, port):
        protocol = PlainTcp(host, port)
        await protocol.send([('test_send', 1, 1)])
        protocol.close()

    with raises(ProtocolError):
        await protocol.send([('test_send', 1, 1)])


@mark.asyncio
async def test_udp():
    sent = []

    async with UdpServer(sent) as (host, port):
        writer = await PlainUdp(host, port)._connect()

        writer.write(b'test_udp\n')
        await sleep(.001)

        writer.close()

    assert sent == [b'test_udp\n']


@mark.asyncio
async def test_send_udp():
    sent = []

    async with UdpServer(sent) as (host, port):
        protocol = PlainUdp(host, port)
        await protocol.send([('test_send_udp', 1, 1)])
        await sleep(.001)
        protocol.close()

    assert sent == [b'test_send_udp 1 1\n']


@mark.parametrize('datatset,data', [
    (
        [('one', 1, 1)],
        b'one 1 1\n'
    ),
    (
        [('two', 2, 2), ('two', 3, 3)],
        b'two 2 2\ntwo 3 3\n'
    ),
])
def test_gzip(datatset, data):
    assert decompress(GzipTcp()._encode(datatset)) == data
