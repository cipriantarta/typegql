from typing import List, Callable, Any, Union

from .arguments import Argument


class _MissingType:
    pass


MISSING = _MissingType()


class Field:
    def __init__(self, *,
                 name: str = '',
                 description: str = '',
                 required: bool = True,
                 mutation: bool = True,
                 arguments: List[Argument] = None,
                 default: Union[Any, Callable] = MISSING):
        self.name = name
        self.description = description
        self.required = required
        self.mutation = mutation
        self.arguments = arguments or list()

        assert isinstance(self.arguments, (tuple, list)), 'Arguments must be a list or tuple'
        self.default = default


class OptionalField(Field):
    """GraphQL field"""

    def __init__(self, **kwargs):
        super().__init__(required=False, **kwargs)


class ReadonlyField(Field):
    """GraphQL field that can't be used in mutations"""

    def __init__(self, **kwargs):
        super().__init__(mutation=False, **kwargs)
