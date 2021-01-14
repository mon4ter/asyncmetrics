from asyncio import sleep as asleep
from time import sleep
from typing import Optional

from pytest import fail, mark, raises

from asyncmetrics import (AvgMetric, AvgMsMetric, AvgNsMetric, AvgUsMetric, CountMetric, Graphite, MaxMetric,
                          MaxMsMetric, MaxNsMetric, MaxUsMetric, Metric, MinMetric, MinMsMetric, MinNsMetric,
                          MinUsMetric, MsMetric, NsMetric, SumMetric, SumMsMetric, SumNsMetric, SumUsMetric, UsMetric,
                          count, time)


class GraphiteMock(Graphite):
    # noinspection PyMissingConstructor
    def __init__(self, name: str):
        self.name = name
        self.sent = []

    def send(self, metric: str, value: int, timestamp: Optional[int] = None):
        self.sent.append((metric, value, timestamp))


@mark.asyncio
async def test_default_graphite():
    assert isinstance(Metric.graphite, Graphite)
    await Metric.graphite.close()


def test_metric():
    metric = 'test.metric'
    assert Metric(metric).metric == metric


def test_invalid_metric():
    with raises(TypeError):
        # noinspection PyTypeChecker
        Metric(1234)


def test_graphite():
    graphite = GraphiteMock('test_graphite')
    assert Metric('some', graphite=graphite)._graphite is graphite


def test_invalid_graphite():
    with raises(TypeError):
        # noinspection PyTypeChecker
        Metric('some', graphite=object())


def test_unset_prefix():
    assert not Metric.prefix


def test_prefix():
    prefix = 'test.prefix'
    Metric.prefix = prefix
    assert Metric.prefix == prefix


def test_invalid_prefix():
    with raises(TypeError):
        # noinspection PyTypeChecker
        Metric.prefix = 345


def test_prefix_delete():
    try:
        del Metric.prefix
    except AttributeError:
        fail("Unexpected AttributeError")

    Metric.prefix = 'some'
    del Metric.prefix
    assert not Metric.prefix


def test_metric_with_prefix():
    prefix = 'test.prefix'
    metric = 'test.metric'
    Metric.prefix = prefix
    assert Metric(metric).metric == '{}.{}'.format(prefix, metric)


def test_metric_with_deleted_prefix():
    prefix = 'test.prefix'
    metric = 'test.metric'
    Metric.prefix = prefix
    assert Metric.prefix == prefix
    del Metric.prefix
    assert Metric(metric).metric == metric


def test_global_graphite():
    graphite = GraphiteMock('test_global_graphite')
    Metric.graphite = graphite
    assert Metric.graphite is graphite


def test_invalid_global_graphite():
    with raises(TypeError):
        Metric.graphite = object()


def test_global_graphite_for_class():
    class MyMetric(Metric):
        graphite = GraphiteMock('test_global_graphite_for_class')

    assert MyMetric.graphite.name == 'test_global_graphite_for_class'


def test_invalid_global_graphite_for_class():
    with raises(TypeError):
        # noinspection PyUnusedLocal
        class MyMetric(Metric):
            graphite = object()


def test_global_prefix():
    class MyMetric(Metric):
        prefix = 'my'

    assert MyMetric('some').metric == 'my.some'


def test_invalid_global_prefix():
    with raises(TypeError):
        # noinspection PyUnusedLocal
        class MyMetric(Metric):
            prefix = 123


def test_send():
    graphite = GraphiteMock('test_send')
    metric = Metric('test_send', graphite=graphite)
    metric.send(1)
    metric.send(2, 3)
    assert graphite.sent == [('test_send', 1, None), ('test_send', 2, 3)]


def test_send_global_graphite():
    Metric.graphite = GraphiteMock('test_send_global_graphite')
    metric = Metric('test_send_global_graphite')
    metric.send(4)
    metric.send(5, 6)
    assert Metric.graphite.sent == [('test_send_global_graphite', 4, None), ('test_send_global_graphite', 5, 6)]


def test_count():
    graphite = GraphiteMock('test_count')
    metric = Metric('test_count', graphite=graphite)

    @metric.count
    def func():
        pass

    func()
    func()
    func()

    assert graphite.sent == [('test_count', 1, None), ('test_count', 1, None), ('test_count', 1, None)]


@mark.asyncio
async def test_count_async():
    graphite = GraphiteMock('test_count_async')
    metric = Metric('test_count_async', graphite=graphite)

    @metric.count
    async def func():
        pass

    await func()
    await func()
    await func()

    assert graphite.sent == [
        ('test_count_async', 1, None),
        ('test_count_async', 1, None),
        ('test_count_async', 1, None),
    ]


def test_time():
    graphite = GraphiteMock('test_time')
    metric = Metric('test_time', graphite=graphite)

    @metric.time
    def func():
        sleep(.001)

    func()
    func()
    func()

    assert all(m == 'test_time' and 1 <= v // 1000000 <= 3 and t is None for m, v, t in graphite.sent)


@mark.asyncio
async def test_time_async():
    graphite = GraphiteMock('test_time_async')
    metric = Metric('test_time_async', graphite=graphite)

    @metric.time
    async def func():
        await asleep(.001)

    await func()
    await func()
    await func()

    assert all(m == 'test_time_async' and 1 <= v // 1000000 <= 3 and t is None for m, v, t in graphite.sent)


def test_subclasses():
    assert MaxMetric('some').metric == 'some.max'
    assert MinMetric('some').metric == 'some.min'
    assert AvgMetric('some').metric == 'some.avg'
    assert SumMetric('some').metric == 'some.sum'
    assert CountMetric('some').metric == 'some.count'
    assert MsMetric('some').metric == 'some.time.ms'
    assert UsMetric('some').metric == 'some.time.us'
    assert NsMetric('some').metric == 'some.time.ns'
    assert MaxMsMetric('some').metric == 'some.max.time.ms'
    assert MaxUsMetric('some').metric == 'some.max.time.us'
    assert MaxNsMetric('some').metric == 'some.max.time.ns'
    assert MinMsMetric('some').metric == 'some.min.time.ms'
    assert MinUsMetric('some').metric == 'some.min.time.us'
    assert MinNsMetric('some').metric == 'some.min.time.ns'
    assert AvgMsMetric('some').metric == 'some.avg.time.ms'
    assert AvgUsMetric('some').metric == 'some.avg.time.us'
    assert AvgNsMetric('some').metric == 'some.avg.time.ns'
    assert SumMsMetric('some').metric == 'some.sum.time.ms'
    assert SumUsMetric('some').metric == 'some.sum.time.us'
    assert SumNsMetric('some').metric == 'some.sum.time.ns'


def test_bare_count():
    Metric.graphite = GraphiteMock('test_bare_count')

    @count
    def func():
        pass

    func()
    func()
    func()

    assert Metric.graphite.sent == [
        ('test_metric.test_bare_count.<locals>.func.count', 1, None),
        ('test_metric.test_bare_count.<locals>.func.count', 1, None),
        ('test_metric.test_bare_count.<locals>.func.count', 1, None),
    ]


def test_bare_count_named():
    Metric.graphite = GraphiteMock('test_bare_count_named')

    @count('test_bare_count_named')
    def func():
        pass

    func()
    func()
    func()

    assert Metric.graphite.sent == [
        ('test_bare_count_named.count', 1, None),
        ('test_bare_count_named.count', 1, None),
        ('test_bare_count_named.count', 1, None),
    ]


def test_bare_time():
    Metric.graphite = GraphiteMock('test_bare_time')

    @time
    def func():
        sleep(.001)

    func()
    func()
    func()

    assert all(
        m == 'test_metric.test_bare_time.<locals>.func.time.ns' and 1 <= v // 1000000 <= 3 and t is None
        for m, v, t in Metric.graphite.sent
    )


def test_bare_time_named():
    Metric.graphite = GraphiteMock('test_bare_time_named')

    @time('test_bare_time_named')
    def func():
        sleep(.001)

    func()
    func()
    func()

    assert all(
        m == 'test_bare_time_named.time.ns' and 1 <= v // 1000000 <= 3 and t is None
        for m, v, t in Metric.graphite.sent
    )


def test_time_classes():
    graphite = GraphiteMock('test_time_classes')
    ms_metric = MsMetric('test_time_classes', graphite=graphite)
    us_metric = UsMetric('test_time_classes', graphite=graphite)
    ns_metric = NsMetric('test_time_classes', graphite=graphite)

    @ms_metric.time
    @us_metric.time
    @ns_metric.time
    def func():
        sleep(.001)

    func()

    ns_data, us_data, ms_data = tuple(graphite.sent)
    assert ms_data[0] == 'test_time_classes.time.ms' and 1 <= ms_data[1] <= 3
    assert us_data[0] == 'test_time_classes.time.us' and 1 <= us_data[1] // 1000 <= 3
    assert ns_data[0] == 'test_time_classes.time.ns' and 1 <= ns_data[1] // 1000000 <= 3
