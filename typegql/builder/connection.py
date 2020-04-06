from dataclasses import dataclass, field
from typing import Generic, Optional, Sequence, TypeVar

from .arguments import Argument
from .types import ID

T = TypeVar("T")


@dataclass
class INode(Generic[T]):
    """Relay node interface"""

    id: ID = field()


@dataclass
class IEdge(Generic[T]):
    """Relay edge interface"""

    node: INode[T] = field(metadata={"description": "Scalar representing your data"})
    cursor: str = field(metadata={"description": "Pagination cursor"})


@dataclass
class IPageInfo:
    """Relay pagination interface"""

    start_cursor: str = field(metadata={"description": "Pagination start cursor"})
    end_cursor: str = field(metadata={"description": "Pagination end cursor"})


@dataclass
class IConnection(Generic[T]):
    """Relay connection interface"""

    edges: Sequence[IEdge[T]] = field(metadata={"description": "Connection edges"})
    page_info: Optional[IPageInfo] = field(
        default=None, metadata={"description": "Pagination information"}
    )

    @classmethod
    def page_arguments(cls):
        return [
            Argument[int](
                "first",
                description="Retrieve only the first `n` nodes of this connection",
            ),
            Argument[int](
                "last",
                description="Retrieve only the last `n` nodes of this connection",
            ),
            Argument[str](
                "before",
                description="Retrieve nodes for this connection before this cursor",
            ),
            Argument[str](
                "after",
                description="Retrieve nodes for this connection after this cursor",
            ),
        ]


@dataclass
class PageInfo(IPageInfo):
    pass


@dataclass
class Connection(IConnection, Generic[T]):
    page_info: Optional[PageInfo] = field(
        default=None, metadata={"description": "Pagination information"}
    )
