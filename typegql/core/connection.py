from typing import Type, get_type_hints, TypeVar, Generic, List

import graphql
from graphql.pyutils import snake_to_camel

from typegql import GraphArgument
from .graph import Graph
from .types import ID
from .info import GraphInfo

T = TypeVar('T', bound=Graph)


class Node(Graph, Generic[T]):
    id: ID

    class Meta:
        id = GraphInfo(required=True)


class Edge(Graph, Generic[T]):
    node: Node[T]
    cursor: str

    class Meta:
        node = GraphInfo(required=True, description='Scalar representing your data')
        cursor = GraphInfo(required=True, description='Pagination cursor')


class PageInfo(Graph):
    has_next: bool
    has_previous: bool
    start_cursor: str
    end_cursor: str

    class Meta:
        has_next = GraphInfo(required=True, description='When paginating forwards, are there more items?')
        has_previous = GraphInfo(required=True, description='When paginating backwards, are there more items?')


class Connection(Graph, Generic[T]):
    edges: List[Edge[T]]
    page_info: PageInfo

    class Meta:
        edges = GraphInfo(required=True, description='Connection edges')
        page_info = GraphInfo(required=True, description='Pagination information')

    @classmethod
    def page_arguments(cls):
        return [
            GraphArgument[int]('first', description='Retrieve only the first `n` nodes of this connection'),
            GraphArgument[int]('last', description='Retrieve only the last `n` nodes of this connection'),
            GraphArgument[str]('before', description='Retrieve nodes for this connection before this cursor'),
            GraphArgument[str]('after', description='Retrieve nodes for this connection after this cursor')
        ]
