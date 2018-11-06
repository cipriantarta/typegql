from __future__ import annotations

import dataclasses
from enum import Enum
from typing import get_type_hints, Type, List, Any, TypeVar, Generic

import graphql

from .types import DateTime, ID


@dataclasses.dataclass
class GraphInfo:
    name: str = dataclasses.field(default='')
    required: bool = dataclasses.field(default=False)
    description: str = dataclasses.field(default='')
    arguments: List[GraphArgument] = dataclasses.field(default_factory=tuple)


class Graph:
    _types = {
        'ID': graphql.GraphQLID,
        'int': graphql.GraphQLInt,
        'str': graphql.GraphQLString,
        'datetime': DateTime(),
        'float': graphql.GraphQLFloat,
    }

    def __init__(self, **kwargs):
        for name, _ in get_type_hints(self.__class__).items():
            if name not in kwargs:
                continue
            setattr(self, name, kwargs.get(name))

    @classmethod
    def get_fields(cls, graph: Type[Graph], is_mutation=False):
        result = dict()
        meta = getattr(graph, 'Meta', None)
        for name, _type in get_type_hints(graph).items():
            info = getattr(meta, name, None)
            if not isinstance(info, GraphInfo):
                info = GraphInfo()
            graph_type = cls.map_type(_type, info=info, is_mutation=is_mutation)
            if not graph_type:
                continue

            args = cls.arguments(info)
            field_name = info.name or name
            if is_mutation:
                result[field_name] = graph_type
            else:
                result[field_name] = graphql.GraphQLField(graph_type,
                                                          description=info.description,
                                                          args=args)

        return result

    @classmethod
    def map_type(cls, _type: Any, info: GraphInfo = None, is_mutation=False):
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
            return cls.add_info(enum_type, info)

        if Graph.is_list(_type):
            inner = cls.map_type(_type.__args__[0], info=info, is_mutation=is_mutation)
            return graphql.GraphQLList(inner)

        if Graph.is_graph(_type):
            return cls.build_object_type(type_name, _type, is_mutation)

        return cls.add_info(cls._types.get(type_name), info)

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
    def build_object_type(cls, type_name, _type, is_mutation=False):
        if is_mutation:
            type_name = f'{type_name}Mutation'
        if type_name in cls._types:
            return cls._types[type_name]
        fields = cls.get_fields(_type, is_mutation=is_mutation)
        if not is_mutation:
            graph_type = graphql.GraphQLObjectType(type_name, fields=fields)
        else:
            graph_type = graphql.GraphQLInputObjectType(type_name, fields=fields)
        cls._types[type_name] = graph_type
        return graph_type

    @classmethod
    def add_info(cls, _type: graphql.GraphQLNamedType, info: GraphInfo):
        if not _type or not isinstance(info, GraphInfo):
            return _type
        _type.description = info.description or _type.description
        if info.required:
            return graphql.GraphQLNonNull(_type)
        return _type

    @classmethod
    def arguments(cls, info: GraphInfo):
        result: graphql.GraphQLArgumentMap = dict()
        for arg in getattr(info, 'arguments', []):
            if not isinstance(arg, GraphArgument):
                continue

            _type = cls.map_type(arg.type, is_mutation=arg.is_input)
            if arg.required:
                _type = graphql.GraphQLNonNull(_type)
            result[arg.name] = graphql.GraphQLArgument(_type, description=arg.description)
        return result


T = TypeVar('T')


class Node(Graph, Generic[T]):
    id: ID

    class Meta:
        id = GraphInfo(required=True)


class Edge(Graph, Generic[T]):
    node: Node[T]
    cursor: str

    class Meta:
        node = GraphInfo(required=True, description='Node identifier')


class Connection(Graph, Generic[T]):
    edges: List[Edge[T]]

    class Meta:
        edges = GraphInfo(required=True, description='Connection edges')

    @classmethod
    def build(cls):
        if 'Node' not in cls._types:
            cls._types['Node'] = graphql.GraphQLInterfaceType('Node', super().get_fields(Node))
        if 'Edge' not in cls._types:
            cls._types['Edge'] = graphql.GraphQLInterfaceType('Edge', super().get_fields(Edge))
        if 'Connection' not in cls._types:
            cls._types['Connection'] = graphql.GraphQLInterfaceType('Connection', super().get_fields(Connection))

    @classmethod
    def get_fields(cls, graph: Type[Graph], is_mutation=False):
        cls.build()
        connection_class = graph.__origin__
        wrapped = graph.__args__[0]

        fields = {}
        for name, _type in get_type_hints(connection_class).items():
            if Graph.is_list(_type):
                inner = _type.__args__[0]
                if inner is Edge[T]:
                    fields[name] = graphql.GraphQLList(Connection.get_edge_field(inner.__origin__, wrapped))
                    continue
            fields[name] = cls.map_type(_type)

        type_name = f'{wrapped.__name__}Connection'
        return graphql.GraphQLObjectType(type_name,
                                         fields=fields,
                                         interfaces=(cls._types.get('Connection'),))

    @classmethod
    def get_edge_field(cls, edge_type, inner: Type[T]):
        fields = dict()
        for name, _type in get_type_hints(edge_type).items():
            if _type is Node[T]:
                fields[name] = cls.get_node_fields(inner)
                continue
            fields[name] = cls.map_type(_type)

        return graphql.GraphQLNonNull(graphql.GraphQLObjectType(
            f'{inner.__name__}Edge',
            fields=fields,
            interfaces=(cls._types.get('Edge'),)
        ))

    @classmethod
    def get_node_fields(cls, _type: Type[T]):
        return graphql.GraphQLNonNull(graphql.GraphQLObjectType(
            f'{_type.__name__}Node',
            fields=super().get_fields(_type),
            interfaces=(cls._types.get('Node'),)
        ))


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
    def get_fields(cls, graph: Type[InputGraph], is_mutation=False):
        return super().get_fields(graph, is_mutation)
