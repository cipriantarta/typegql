from typing import Generic, TypeVar, List, Type, Any

T = TypeVar('T', bound='Graph')


class GraphArgument:
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


class GraphArgumentList(GraphArgument):
    @property
    def type(self):
        return List[self._type]


class InputArgument(GraphArgument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_input = True


class RequiredArgument(GraphArgument, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = True


class ListRequiredArgument(GraphArgumentList, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = True

    @property
    def type(self):
        return List[self._type]


class RequiredInputArgument(GraphArgument, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = True
        self.is_input = True


class ListInputArgument(GraphArgumentList, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_input = True

    @property
    def type(self):
        return List[self._type]


class ListRequiredInputArgument(GraphArgumentList, Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = True
        self.is_input = True

    @property
    def type(self):
        return List[self._type]


Argument = GraphArgument
ArgumentList = GraphArgumentList
