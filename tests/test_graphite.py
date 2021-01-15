from asyncio import sleep
from typing import List

from pytest import mark, raises

from asyncmetrics import Graphite, PlainTcp, ProtocolError


class SomeError(Exception):
    pass


class ProtocolMock(PlainTcp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent = []

    async def send(self, dataset: List[tuple]):
        if any(n == 'test_send_failed' for n, _, _ in dataset):
            raise ProtocolError
        elif any(n == 'test_some_error' for n, _, _ in dataset):
            raise SomeError
        elif any(n == 'test_flush' for n, _, _ in dataset):
            await sleep(.001)

        self.sent.extend(dataset)


@mark.asyncio
async def test_queue_size():
    queue_size = 10
    protocol = ProtocolMock()
    graphite = Graphite(protocol=protocol, queue_size=queue_size)

    for _ in range(queue_size * 2):
        graphite.send('test_queue_size', 1)

    await sleep(.001)
    await graphite.close()
    assert len(protocol.sent) == queue_size


@mark.asyncio
async def test_not_running():
    protocol = ProtocolMock()
    graphite = Graphite(protocol=protocol)
    await sleep(.001)
    await graphite.close()
    graphite.send('test_not_running', 1)
    await sleep(.001)
    assert not protocol.sent


@mark.asyncio
async def test_invalid():
    protocol = ProtocolMock()
    graphite = Graphite(protocol=protocol)
    # noinspection PyTypeChecker
    graphite.send('test_invalid', 'one')
    await sleep(.001)
    await graphite.close()
    assert not protocol.sent


@mark.asyncio
async def test_send():
    protocol = ProtocolMock()
    graphite = Graphite(protocol=protocol, flush_interval=0)
    graphite.send('test_send', 1)
    await sleep(.001)
    assert len(protocol.sent) == 1
    await graphite.close()


@mark.asyncio
async def test_send_failed():
    protocol = ProtocolMock()
    graphite = Graphite(protocol=protocol, flush_interval=0)
    graphite.send('test_send_failed', 1)
    await sleep(.001)
    await graphite.close()
    assert not protocol.sent
    assert graphite._queue.get_nowait()[0] == 'test_send_failed'


@mark.asyncio
async def test_some_error():
    protocol = ProtocolMock()
    graphite = Graphite(protocol=protocol)
    graphite.send('test_some_error', 1)
    await sleep(.001)
    await graphite.close()

    with raises(SomeError):
        await graphite._sender_task


@mark.asyncio
async def test_flush():
    protocol = ProtocolMock()
    graphite = Graphite(protocol=protocol, flush_interval=0)
    graphite.send('test_flush', 1)
    await sleep(.001)
    assert not protocol.sent
    assert graphite._queue.empty()
    graphite.send('test_flush.no_sleep', 1)
    await graphite.close()
    assert len(protocol.sent) == 2
