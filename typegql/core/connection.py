from typing import TypeVar, Generic, List

from .arguments import Argument
from .fields import Field
from .graph import Graph
from .types import ID

T = TypeVar('T', bound=Graph)


class Node(Graph, Generic[T]):
    id: ID = Field()


class Edge(Graph, Generic[T]):
    node: Node[T] = Field(description='Scalar representing your data')
    cursor: str = Field(description='Pagination cursor')


class PageInfo(Graph):
    has_next: bool = Field(description='When paginating forwards, are there more items?')
    has_previous: bool = Field(description='When paginating backwards, are there more items?')
    start_cursor: str = Field(description='Pagination start cursor')
    end_cursor: str = Field(description='Pagination end cursor')


class Connection(Graph, Generic[T]):
    edges: List[Edge[T]] = Field(description='Connection edges')
    page_info: PageInfo = Field(description='Pagination information')

    @classmethod
    def page_arguments(cls):
        return [
            Argument[int]('first', description='Retrieve only the first `n` nodes of this connection'),
            Argument[int]('last', description='Retrieve only the last `n` nodes of this connection'),
            Argument[str]('before', description='Retrieve nodes for this connection before this cursor'),
            Argument[str]('after', description='Retrieve nodes for this connection after this cursor')
        ]
