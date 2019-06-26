from typing import Optional

from pytest import raises, fail

from asyncmetrics import Graphite, Metric


class GraphiteDummy(Graphite):
    # noinspection PyMissingConstructor
    def __init__(self):
        pass

    def send(self, metric: str, value: int, timestamp: Optional[int] = None):
        pass


def test_metric():
    metric = 'test.metric'
    assert Metric(metric).metric == metric


def test_invalid_metric():
    with raises(TypeError):
        # noinspection PyTypeChecker
        Metric(1234)


def test_graphite():
    graphite = GraphiteDummy()
    # noinspection PyProtectedMember
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
    graphite = GraphiteDummy()
    Metric.graphite = graphite
    assert Metric.graphite is graphite


def test_invalid_global_graphite():
    with raises(TypeError):
        Metric.graphite = object()
