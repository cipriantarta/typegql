from __future__ import annotations

import dataclasses
from enum import Enum
from typing import get_type_hints, Type, List, Any, Generic, TypeVar, Tuple

import graphql

from .types import DateTime, ID

_TYPES = {
    'ID': graphql.GraphQLID,
    'int': graphql.GraphQLInt,
    'str': graphql.GraphQLString,
    'datetime': DateTime(),
    'float': graphql.GraphQLFloat,
}


@dataclasses.dataclass
class GraphInfo:
    name: str = dataclasses.field(default='')
    required: bool = dataclasses.field(default=False)
    description: str = dataclasses.field(default='')
    arguments: List[GraphArgument] = dataclasses.field(default_factory=tuple)


class Graph:
    def __init__(self, **kwargs):
        for name, _ in get_type_hints(self.__class__).items():
            if name not in kwargs:
                continue
            setattr(self, name, kwargs.get(name))

    @staticmethod
    def get_fields(graph: Type[Graph]):
        result = dict()
        meta = getattr(graph, 'Meta', None)
        for name, _type in get_type_hints(graph).items():
            info = getattr(meta, name, None)
            graph_type = Graph.map_type(_type, info=info)
            if not graph_type:
                continue

            args = Graph.arguments(info)
            result[name] = graphql.GraphQLField(graph_type, description=getattr(info, 'description', ''), args=args)

        return result

    @staticmethod
    def map_type(_type: Any, info: GraphInfo=None):
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

        result = _TYPES.get(type_name)
        result = Graph.add_info(result, info)

        if result:
            return result

        if Graph.is_enum(_type):
            if type_name in _TYPES:
                return _TYPES.get(type_name)
            enum_type = graphql.GraphQLEnumType(type_name, _type)
            _TYPES[type_name] = enum_type
            return Graph.add_info(enum_type, info)

        if Graph.is_list(_type):
            inner = Graph.map_type(_type.__args__[0])
            return graphql.GraphQLList(inner)

        if Graph.is_graph(_type):
            return Graph.build_object_type(type_name, _type)

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

    @staticmethod
    def build_object_type(type_name, _type):
        if type_name in _TYPES:
            return _TYPES[type_name]
        fields = Graph.get_fields(_type)
        graph_type = graphql.GraphQLObjectType(type_name, fields=fields)
        _TYPES[type_name] = graph_type
        return graph_type

    @staticmethod
    def add_info(_type: graphql.GraphQLNamedType, info: GraphInfo):
        if not _type or not isinstance(info, GraphInfo):
            return _type
        _type.name = info.name or _type.name
        _type.description = info.description or _type.description
        if info.required:
            return graphql.GraphQLNonNull(_type)
        return _type

    @staticmethod
    def arguments(info: GraphInfo):
        result: graphql.GraphQLArgumentMap = dict()
        for arg in getattr(info, 'arguments', []):
            if not isinstance(arg, GraphArgument):
                continue

            _type = Graph.map_type(arg.type)
            if arg.required:
                _type = graphql.GraphQLNonNull(_type)
            result[arg.name] = graphql.GraphQLArgument(_type, description=arg.description)
        return result


T = TypeVar('T', bound=Graph)


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

    @staticmethod
    def build():
        if 'Node' not in _TYPES:
            _TYPES['Node'] = graphql.GraphQLInterfaceType('Node', Graph.get_fields(Node))
        if 'Edge' not in _TYPES:
            _TYPES['Edge'] = graphql.GraphQLInterfaceType('Edge', Graph.get_fields(Edge))
        if 'Connection' not in _TYPES:
            _TYPES['Connection'] = graphql.GraphQLInterfaceType('Connection', Graph.get_fields(Connection))

    @staticmethod
    def get_fields(graph: Type[Graph]):
        Connection.build()
        connection_class = graph.__origin__
        wrapped = graph.__args__[0]

        fields = {}
        for name, _type in get_type_hints(connection_class).items():
            if Graph.is_list(_type):
                inner = _type.__args__[0]
                if inner is Edge[T]:
                    fields[name] = graphql.GraphQLList(Connection.get_edge_field(inner.__origin__, wrapped))
                    continue
            fields[name] = Graph.map_type(_type)

        type_name = f'{wrapped.__name__}sConnection'
        return graphql.GraphQLObjectType(type_name,
                                         fields=fields,
                                         interfaces=(_TYPES.get('Connection'),))

    @staticmethod
    def get_edge_field(edge_type, inner: Type[T]):
        fields = dict()
        for name, _type in get_type_hints(edge_type).items():
            if _type is Node[T]:
                fields[name] = Connection.get_node_fields(inner)
                continue
            fields[name] = Graph.map_type(_type)

        return graphql.GraphQLNonNull(graphql.GraphQLObjectType(
            f'{inner.__name__}Edge',
            fields=fields,
            interfaces=(_TYPES.get('Edge'),)
        ))

    @staticmethod
    def get_node_fields(_type: Type[T]):
        return graphql.GraphQLNonNull(graphql.GraphQLObjectType(
            f'{_type.__name__}Node',
            fields=Graph.get_fields(_type),
            interfaces=(_TYPES.get('Node'),)
        ))


@dataclasses.dataclass
class GraphArgument(Generic[T]):
    name: str
    description: str = dataclasses.field(default='')
    required: bool = dataclasses.field(default=False)

    @property
    def type(self):
        return self.__orig_class__.__args__[0]
