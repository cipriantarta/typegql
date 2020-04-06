from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


class Argument(Generic[T]):
    def __init__(
        self,
        name: str = "",
        description: str = "",
        required: bool = False,
        is_input: bool = False,
    ):
        self._type = None
        self.name = name
        self.description = description
        self.required = required
        self.is_input = is_input

    def __class_getitem__(cls, _type):
        instance = cls()
        instance._type = _type
        return instance

    def __call__(
        self,
        name: str = "",
        description: str = "",
        required: bool = False,
        is_input: bool = False,
    ):
        self.name = name
        self.description = description
        self.required = required
        self.is_input = is_input
        return self

    @property
    def type(self):
        return self._type


class RequiredArgument(Argument, Generic[T]):
    def __call__(
        self,
        name: str = "",
        description: str = "",
        required: bool = False,
        is_input: bool = False,
    ):
        return super().__call__(name, description, True, is_input)


class ArgumentList(Argument, Generic[T]):
    @property
    def type(self):
        return Sequence[self._type]


class RequiredArgumentList(RequiredArgument, Generic[T]):
    @property
    def type(self):
        return Sequence[self._type]


class InputArgument(Argument, Generic[T]):
    def __call__(
        self,
        name: str = "",
        description: str = "",
        required: bool = False,
        is_input: bool = False,
    ):
        return super().__call__(name, description, required, True)


class RequiredInputArgument(Argument, Generic[T]):
    def __call__(
        self,
        name: str = "",
        description: str = "",
        required: bool = False,
        is_input: bool = False,
    ):
        return super().__call__(name, description, True, True)


class ListInputArgument(InputArgument, Generic[T]):
    @property
    def type(self):
        return Sequence[self._type]


class RequiredListInputArgument(RequiredInputArgument, Generic[T]):
    @property
    def type(self):
        return Sequence[self._type]
