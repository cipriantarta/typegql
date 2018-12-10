from typing import Type, get_type_hints, TypeVar, Generic, List

import graphql
from graphql.pyutils import snake_to_camel

from .types import ID
from .info import GraphInfo

T = TypeVar('T')


class Node(Generic[T]):
    id: ID

    class Meta:
        id = GraphInfo(required=True)


class Edge(Generic[T]):
    node: Node[T]
    cursor: str

    class Meta:
        node = GraphInfo(required=True, description='Scalar representing your data')
        cursor = GraphInfo(required=True, description='Pagination cursor')


class PageInfo:
    has_next: bool
    has_previous: bool
    start_cursor: str
    end_cursor: str

    class Meta:
        has_next = GraphInfo(required=True, description='When paginating forwards, are there more items?')
        has_previous = GraphInfo(required=True, description='When paginating backwards, are there more items?')


class Connection(Generic[T]):
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
    def get_fields(cls, graph: Type, is_mutation=False, camelcase=True):
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
