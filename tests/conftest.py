import pytest
from graphql import get_introspection_query

from typegql.core.schema import Schema
from examples.library.query import Query


def pytest_collection_modifyitems(items):
    for item in items:
        if not hasattr(item, 'fixturenames'):
            setattr(item, 'fixturenames', list())
        item.add_marker(pytest.mark.asyncio)


@pytest.fixture
def schema():
    schema = Schema(Query)
    return schema


@pytest.fixture
def introspection_query():
    return get_introspection_query()
