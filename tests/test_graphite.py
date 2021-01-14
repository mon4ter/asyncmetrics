from asyncio import sleep
from typing import List

from aiographite.aiographite import AIOGraphite, AioGraphiteSendException
from pytest import mark, raises

from asyncmetrics import Graphite


class SomeError(Exception):
    pass


class AIOGraphiteMock(AIOGraphite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent = []

    async def _connect(self):
        pass

    async def send_multiple(self, dataset: List[tuple], timestamp: int = None) -> None:
        if any(n == 'test_send_failed' for n, _, _ in dataset):
            raise AioGraphiteSendException
        elif any(n == 'test_some_error' for n, _, _ in dataset):
            raise SomeError
        elif any(n == 'test_flush' for n, _, _ in dataset):
            await sleep(.001)

        self.sent.extend(dataset)

    async def close(self):
        pass


class GraphiteMock(Graphite):
    async def _connect(self) -> AIOGraphite:
        args, kwargs = self._connect_args
        return AIOGraphiteMock(*args, **kwargs)


@mark.asyncio
async def test_queue_size():
    queue_size = 10

    graphite = GraphiteMock(queue_size=queue_size)

    for _ in range(queue_size * 2):
        graphite.send('test_queue_size', 1)

    await sleep(.001)
    await graphite.close()
    assert len(graphite._conn.sent) == queue_size


@mark.asyncio
async def test_not_running():
    graphite = GraphiteMock()
    await sleep(.001)
    await graphite.close()
    graphite.send('test_not_running', 1)
    await sleep(.001)
    assert not graphite._conn.sent


@mark.asyncio
async def test_invalid():
    graphite = GraphiteMock()
    # noinspection PyTypeChecker
    graphite.send('test_invalid', 'one')
    await sleep(.001)
    await graphite.close()
    assert not graphite._conn.sent


@mark.asyncio
async def test_cancel():
    graphite = GraphiteMock()
    await graphite.close()
    assert graphite._conn is None


@mark.asyncio
async def test_send():
    graphite = GraphiteMock(flush_interval=0)
    graphite.send('test_send', 1)
    await sleep(.001)
    assert len(graphite._conn.sent) == 1
    await graphite.close()


@mark.asyncio
async def test_send_failed():
    graphite = GraphiteMock(flush_interval=0)
    graphite.send('test_send_failed', 1)
    await sleep(.001)
    await graphite.close()
    assert not graphite._conn.sent
    assert graphite._queue.get_nowait()[0] == 'test_send_failed'


@mark.asyncio
async def test_some_error():
    graphite = GraphiteMock()
    graphite.send('test_some_error', 1)
    await sleep(.001)
    await graphite.close()

    with raises(SomeError):
        await graphite._sender_task


@mark.asyncio
async def test_flush():
    graphite = GraphiteMock(flush_interval=0)
    graphite.send('test_flush', 1)
    await sleep(.001)
    assert not graphite._conn.sent
    assert graphite._queue.empty()
    graphite.send('test_flush.no_sleep', 1)
    await graphite.close()
    assert len(graphite._conn.sent) == 2


@mark.asyncio
async def test_connect():
    graphite = Graphite(protocol=object())

    with raises(AioGraphiteSendException):
        await graphite._connect()
