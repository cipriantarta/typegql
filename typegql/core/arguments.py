import dataclasses
from typing import Generic, TypeVar, List

T = TypeVar('T', bound='Graph')


@dataclasses.dataclass
class GraphArgument(Generic[T]):
    name: str
    description: str = ''
    required: bool = False
    is_input: bool = False

    @property
    def type(self):
        return self.__orig_class__.__args__[0]


@dataclasses.dataclass
class GraphArgumentList(Generic[T]):
    name: str
    description: str = ''
    required: bool = False
    is_input: bool = False

    @property
    def type(self):
        return List[self.__orig_class__.__args__[0]]


Argument = GraphArgument
ArgumentList = GraphArgumentList
