from typing import Generic, TypeVar, List, Type, Any

T = TypeVar('T', bound='Graph')


class Argument:
    def __init__(self, _type: Type[Any], name: str, description: str = '',
                 required: bool = False,
                 is_input: bool = False):
        self._type = _type
        self.name = name
        self.description = description
        self.required = required
        self.is_input = is_input

    def __class_getitem__(cls, *args, **kwargs):
        assert len(args) == 1, 'GraphArgument container accepts a single argument'
        item = args[0]
        return cls(item, name='')

    def __call__(self, name: str, *args, **kwargs):
        self.name = name
        return self

    @property
    def type(self):
        return self._type


class RequiredArgument(Argument, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = True


class ArgumentList(Argument):
    @property
    def type(self):
        return List[self._type]


class RequiredArgumentList(RequiredArgument):
    @property
    def type(self):
        return List[self._type]


class InputArgument(Argument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_input = True


class RequiredInputArgument(Argument, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = True
        self.is_input = True


class ListInputArgument(ArgumentList, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_input = True

    @property
    def type(self):
        return List[self._type]


class RequiredListInputArgument(ArgumentList, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = True
        self.is_input = True

    @property
    def type(self):
        return List[self._type]
