from aiographite import AIOGraphite
from pytest import mark

from asyncmetrics import Graphite


class AIOGraphiteDummy(AIOGraphite):
    def __init__(self, graphite_server='127.0.0.1', *args, **kwargs):
        super().__init__(graphite_server, *args, **kwargs)

    async def _connect(self):
        return self

    async def send_multiple(self, *_, **__):
        pass

    async def close(self):
        pass


@mark.asyncio
async def test_conn_set(event_loop):
    conn = AIOGraphiteDummy(loop=event_loop)
    graphite = Graphite(conn)
    # noinspection PyProtectedMember
    assert graphite._conn is conn
    await graphite.close()


@mark.asyncio
async def test_limit_set(event_loop):
    conn = AIOGraphiteDummy(loop=event_loop)
    limit = 500

    graphite_1 = Graphite(conn)
    # noinspection PyProtectedMember
    assert graphite_1._limit == Graphite.DEFAULT_LIMIT
    await graphite_1.close()

    graphite_2 = Graphite(conn, limit=limit)
    # noinspection PyProtectedMember
    assert graphite_2._limit == limit
    await graphite_2.close()
