import functools
from typing import List, Any, Type

from .arguments import Argument
from .connection import Connection
from .info import GraphInfo

_cleanups = []


def cache(func):
    cached = functools.lru_cache()(func)
    _cleanups.append(cached.cache_clear)

    @functools.wraps(func)
    def inner(*args, **kwds):
        try:
            return cached(*args, **kwds)
        except TypeError:
            pass  # All real errors (not unhashable args) are raised below.
        return func(*args, **kwds)

    return inner


class Field:
    def __init__(self, _type: Type[Any], name: str = None, description: str = None, required: bool = False,
                 arguments: List[Argument] = None, mutation: bool = True):
        """
        Wraps a field intro a GraphQLField
        :param _type: original type
        :param name: field name as it should show in introspection
        :param description: field description as it should show in introspection
        :param required: is it nullable?
        :param arguments: GraphQL arguments for this field
        :param mutation: Should it be available for GraphQL mutations?
        """
        self._type = _type
        self._name = name
        self._description = description
        self.required = required
        self.arguments = arguments
        self.mutation = mutation

    @cache
    def __class_getitem__(cls, *args):
        assert len(args) == 1, 'Field container accepts a single argument'
        item = args[0]
        return cls(item)

    def __call__(self, *args, **kwargs):
        self._name = kwargs.get('name')
        description = kwargs.get('description')
        if description:
            self._description = description
        self.required = kwargs.get('required', False)
        self.arguments = kwargs.get('arguments', list())
        return self

    @property
    def type(self):
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def info(self) -> GraphInfo:
        return GraphInfo(name=self.name, description=self.description, required=self.required,
                         arguments=self.arguments, mutation=self.mutation)


class ListField(Field):
    """GraphQL list field"""

    def __init__(self, _type: Type[Any], name: str = None, description: str = None, required: bool = False,
                 arguments: List[Argument] = None):
        _type = List[_type]
        super().__init__(_type, name, description, required, arguments)


class InputField(Field):
    """GraphQL field which can also be used in mutations"""

    def __init__(self, _type: Type[Any], name: str = None, description: str = None, required: bool = False,
                 arguments: List[Argument] = None):
        super().__init__(_type, name, description, required, arguments, mutation=True)


class RequiredField(Field):
    """GraphQL Non NULL field"""

    def __init__(self, _type: Type[Any], name: str = None, description: str = None, required: bool = True,
                 arguments: List[Argument] = None):
        super().__init__(_type, name, description, required, arguments)


class ReadonlyField(Field):
    """GraphQL Field that can't be used in mutations"""

    def __init__(self, _type: Type[Any], name: str = None, description: str = None, required: bool = False,
                 arguments: List[Argument] = None):
        super().__init__(_type, name, description, required, arguments, mutation=False)


class ConnectionField(Field):
    """Relay connection field"""

    def __call__(self, *args, **kwargs):
        connection_class = kwargs.get('connection_class', Connection)
        self._type = connection_class[self._type]
        return super().__call__(*args, **kwargs)
