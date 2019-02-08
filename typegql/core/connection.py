from typing import TypeVar, Generic, List

from .arguments import Argument
from .fields import Field, OptionalField
from .graph import Graph
from .types import ID

T = TypeVar('T', bound=Graph)


class INode(Graph, Generic[T]):
    id: ID = Field()


class IEdge(Graph, Generic[T]):
    node: INode[T] = Field(description='Scalar representing your data')
    cursor: str = Field(description='Pagination cursor')


class IPageInfo(Graph):
    start_cursor: str = Field(description='Pagination start cursor')
    end_cursor: str = Field(description='Pagination end cursor')


class IConnection(Graph, Generic[T]):
    edges: List[IEdge[T]] = Field(description='Connection edges')
    page_info: IPageInfo = OptionalField(description='Pagination information')

    @classmethod
    def page_arguments(cls):
        return [
            Argument[int]('first', description='Retrieve only the first `n` nodes of this connection'),
            Argument[int]('last', description='Retrieve only the last `n` nodes of this connection'),
            Argument[str]('before', description='Retrieve nodes for this connection before this cursor'),
            Argument[str]('after', description='Retrieve nodes for this connection after this cursor')
        ]


class PageInfo(IPageInfo):
    pass


class Connection(IConnection, Generic[T]):
    page_info: PageInfo = OptionalField(description='Pagination information')
