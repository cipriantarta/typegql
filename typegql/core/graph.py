from __future__ import annotations

import dataclasses
from enum import Enum
from typing import get_type_hints, Type, List, Any, TypeVar, Generic

import graphql
from graphql.pyutils import snake_to_camel

from .types import DateTime, ID, Dictionary


@dataclasses.dataclass
class GraphInfo:
    name: str = dataclasses.field(default='')
    required: bool = dataclasses.field(default=False)
    use_in_mutation: bool = dataclasses.field(default=True)
    description: str = dataclasses.field(default='')
    arguments: List[GraphArgument] = dataclasses.field(default_factory=list)


class Graph:
    _types = {
        'ID': graphql.GraphQLID,
        'bool': graphql.GraphQLBoolean,
        'int': graphql.GraphQLInt,
        'float': graphql.GraphQLFloat,
        'str': graphql.GraphQLString,
        'datetime': DateTime(),
        'Dict': Dictionary()
    }

    def __init__(self, **kwargs):
        for name, _ in get_type_hints(self.__class__).items():
            if name not in kwargs:
                continue
            setattr(self, name, kwargs.get(name))

    @classmethod
    def get_fields(cls, graph: Type[Graph], is_mutation=False, camelcase=True):
        result = dict()
        meta = getattr(graph, 'Meta', None)
        for name, _type in get_type_hints(graph).items():
            info = getattr(meta, name, GraphInfo())
            assert isinstance(info, GraphInfo), f'{graph.__name__} info for `{name}` MUST be of type `GraphInfo`'

            if is_mutation and not info.use_in_mutation:
                continue

            graph_type = cls.map_type(_type, is_mutation=is_mutation)
            if not graph_type:
                continue

            if cls.is_connection(_type):
                info.arguments.extend(cls.page_arguments())

            if info.required:
                graph_type = graphql.GraphQLNonNull(graph_type)

            args = cls.arguments(info, camelcase)
            field_name = info.name or name
            if camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            if is_mutation:
                result[field_name] = graph_type
            else:
                result[field_name] = graphql.GraphQLField(graph_type,
                                                          description=info.description,
                                                          args=args)

        return result

    @classmethod
    def map_type(cls, _type: Any, is_mutation=False):
        if isinstance(_type, graphql.GraphQLType):
            return _type
        try:
            type_name = _type.__name__
        except AttributeError:
            type_name = _type._name

        if not type_name:
            type_name = _type.__origin__.__name__

        if Graph.is_connection(_type):
            return Connection.get_fields(_type)

        if Graph.is_enum(_type):
            if type_name in cls._types:
                return cls._types.get(type_name)
            enum_type = graphql.GraphQLEnumType(type_name, _type)
            cls._types[type_name] = enum_type
            return enum_type

        if Graph.is_list(_type):
            inner = cls.map_type(_type.__args__[0], is_mutation=is_mutation)
            return graphql.GraphQLList(inner)

        if Graph.is_graph(_type):
            return cls.build_object_type(type_name, _type, is_mutation=is_mutation)

        return cls._types.get(type_name)

    @staticmethod
    def is_list(_type: Any) -> bool:
        try:
            return issubclass(_type.__origin__, List)
        except AttributeError:
            return False

    @staticmethod
    def is_enum(_type: Any) -> bool:
        try:
            return issubclass(_type, Enum)
        except TypeError:
            return False

    @staticmethod
    def is_graph(_type: Any) -> bool:
        try:
            return issubclass(_type, Graph)
        except TypeError:
            return False

    @staticmethod
    def is_connection(_type: Any) -> bool:
        try:
            return _type.__origin__ is Connection or issubclass(_type.__origin__, Connection)
        except (TypeError, AttributeError):
            return False

    @classmethod
    def build_object_type(cls, type_name, _type, info: GraphInfo=None, is_mutation=False):
        if is_mutation:
            type_name = f'{type_name}Mutation'
        if type_name in cls._types:
            return cls._types[type_name]
        fields = cls.get_fields(_type, is_mutation=is_mutation)
        if not is_mutation:
            graph_type = graphql.GraphQLObjectType(type_name, fields=fields)
        else:
            graph_type = graphql.GraphQLInputObjectType(type_name, fields=fields)
        if isinstance(info, GraphInfo):
            if info.required:
                graph_type = graphql.GraphQLNonNull(graph_type)
        cls._types[type_name] = graph_type
        return graph_type

    @classmethod
    def arguments(cls, info: GraphInfo, camelcase=True):
        result: graphql.GraphQLArgumentMap = dict()
        for arg in getattr(info, 'arguments', []):
            if not isinstance(arg, GraphArgument):
                continue

            _type = cls.map_type(arg.type, is_mutation=arg.is_input)
            if arg.required:
                _type = graphql.GraphQLNonNull(_type)
            arg_name = snake_to_camel(arg.name, False) if camelcase else arg.name
            result[arg_name] = graphql.GraphQLArgument(_type, description=arg.description)
        return result

    @classmethod
    def page_arguments(cls):
        return [
            GraphArgument[int]('first', description='Retrieve only the first `n` nodes of this connection'),
            GraphArgument[int]('last', description='Retrieve only the last `n` nodes of this connection'),
            GraphArgument[str]('before', description='Retrieve nodes for this connection before this cursor'),
            GraphArgument[str]('after', description='Retrieve nodes for this connection after this cursor')
        ]


T = TypeVar('T')


class Node(Graph, Generic[T]):
    id: ID

    class Meta:
        id = GraphInfo(required=True)


class Edge(Graph, Generic[T]):
    node: Node[T]
    cursor: str

    class Meta:
        node = GraphInfo(required=True, description='Scalar representing your data')
        cursor = GraphInfo(required=True, description='Pagination cursor')


class PageInfo(Graph):
    has_next: bool
    has_previous: bool
    start_cursor: str
    end_cursor: str

    class Meta:
        has_next = GraphInfo(required=True, description='When paginating forwards, are there more items?')
        has_previous = GraphInfo(required=True, description='When paginating backwards, are there more items?')


class Connection(Graph, Generic[T]):
    edges: List[Edge[T]]
    page_info: PageInfo

    class Meta:
        edges = GraphInfo(required=True, description='Connection edges')
        page_info = GraphInfo(required=True, description='Pagination information')

    @classmethod
    def build(cls):
        if 'Node' not in cls._types:
            cls._types['Node'] = graphql.GraphQLInterfaceType('Node', super().get_fields(Node))
        if 'Edge' not in cls._types:
            cls._types['Edge'] = graphql.GraphQLInterfaceType('Edge', super().get_fields(Edge))
        if 'PageInfo' not in cls._types:
            cls._types['PageInfo'] = graphql.GraphQLObjectType('PageInfo', super().get_fields(PageInfo))
        if 'Connection' not in cls._types:
            cls._types['Connection'] = graphql.GraphQLInterfaceType('Connection', super().get_fields(Connection))

    @classmethod
    def get_fields(cls, graph: Type[Graph], is_mutation=False, camelcase=True):
        if not Graph.is_connection(graph):
            return super().get_fields(graph, is_mutation=is_mutation, camelcase=camelcase)

        cls.build()
        connection_class = graph.__origin__
        wrapped = graph.__args__[0]

        fields = {}
        meta = getattr(graph, 'Meta', None)
        for name, _type in get_type_hints(connection_class).items():
            info = getattr(meta, name, GraphInfo())
            if Graph.is_list(_type) and _type.__args__[0] is Edge[T]:
                inner = _type.__args__[0]
                graph_type = graphql.GraphQLList(cls.get_edge_field(inner.__origin__, wrapped, camelcase=camelcase))
            else:
                graph_type = cls.map_type(_type)
            if info.required:
                graph_type = graphql.GraphQLNonNull(graph_type)

            field_name = info.name or name
            if camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            fields[field_name] = graphql.GraphQLField(graph_type, description=info.description)

        type_name = f'{wrapped.__name__}Connection'
        return graphql.GraphQLObjectType(type_name,
                                         fields=fields,
                                         interfaces=(cls._types.get('Connection'),))

    @classmethod
    def get_edge_field(cls, edge_type, inner: Type[T], camelcase=True):
        fields = dict()
        meta = getattr(edge_type, 'Meta', None)
        for name, _type in get_type_hints(edge_type).items():
            info = getattr(meta, name, GraphInfo())
            if _type is Node[T]:
                graph_type = cls.get_node_fields(inner)
            else:
                graph_type = cls.map_type(_type)
            if info.required:
                graph_type = graphql.GraphQLNonNull(graph_type)
            field_name = info.name or name
            if camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            fields[field_name] = graph_type

        return graphql.GraphQLNonNull(graphql.GraphQLObjectType(
            f'{inner.__name__}Edge',
            fields=fields,
            interfaces=(cls._types.get('Edge'),)
        ))

    @classmethod
    def get_node_fields(cls, _type: Type[T]):
        return graphql.GraphQLObjectType(
            f'{_type.__name__}Node',
            fields=super().get_fields(_type),
            interfaces=(cls._types.get('Node'),)
        )


@dataclasses.dataclass
class GraphArgument(Generic[T]):
    name: str
    description: str = ''
    required: bool = False
    is_input: bool = False

    @property
    def type(self):
        return self.__orig_class__.__args__[0]


class InputGraph(Graph):
    @classmethod
    def get_fields(cls, graph: Type[InputGraph], is_mutation=False, camelcase=True):
        return super().get_fields(graph, is_mutation, camelcase)
