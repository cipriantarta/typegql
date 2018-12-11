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


@dataclasses.dataclass
class InputArgument(GraphArgument, Generic[T]):
    name: str
    description: str = ''
    required: bool = False
    is_input: bool = True


@dataclasses.dataclass
class RequiredArgument(GraphArgument, Generic[T]):
    name: str
    description: str = ''
    required: bool = True
    is_input: bool = False


@dataclasses.dataclass
class ListRequiredArgument(GraphArgumentList, Generic[T]):
    name: str
    description: str = ''
    required: bool = True
    is_input: bool = False


@dataclasses.dataclass
class RequiredInputArgument(GraphArgument, Generic[T]):
    name: str
    description: str = ''
    required: bool = True
    is_input: bool = True


@dataclasses.dataclass
class ListInputArgument(GraphArgumentList, Generic[T]):
    name: str
    description: str = ''
    required: bool = False
    is_input: bool = True


@dataclasses.dataclass
class ListRequiredInputArgument(GraphArgumentList, Generic[T]):
    name: str
    description: str = ''
    required: bool = True
    is_input: bool = True


Argument = GraphArgument
ArgumentList = GraphArgumentList
