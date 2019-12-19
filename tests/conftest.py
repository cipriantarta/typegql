import pytest
from graphql import get_introspection_query

from typegql.core.schema import Schema
from examples.library.query import Query
from examples.library.mutation import Mutation
from examples.library.subscription import Subscription


def pytest_collection_modifyitems(items):
    for item in items:
        if not hasattr(item, 'fixturenames'):
            setattr(item, 'fixturenames', list())
        if not hasattr(item, 'obj'):
            setattr(item, 'obj', None)
        item.add_marker(pytest.mark.asyncio)


@pytest.fixture
def schema():
    schema = Schema(Query, mutation=Mutation, subscription=Subscription)
    return schema


@pytest.fixture()
def schema_type():
    return Schema


@pytest.fixture
def introspection_query():
    return get_introspection_query()
