from typing import Any, Dict, Optional, Type

from graphql import (
    GraphQLArgumentMap,
    GraphQLField,
    GraphQLFieldMap,
    GraphQLInterfaceType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType
)

from . import Builder
from .connection import IConnection, IEdge, INode, IPageInfo, T
from .utils import is_connection, is_required, is_sequence

GraphQLOutputTypeMap = Dict[str, GraphQLOutputType]


class QueryBuilder(Builder):
    def __init__(self,
                 camelcase: bool = True,
                 types: Optional[GraphQLOutputTypeMap] = None):
        super().__init__(camelcase)

    def arguments(self, definition: Optional[Dict]) -> Optional[GraphQLArgumentMap]:
        pass

    def fields(self, source: Type[Any]) -> GraphQLFieldMap:
        result: GraphQLFieldMap = {}
        if is_connection(source):
            return self.build_connection(source)

        for build_type in self.build_type(source):
            if build_type.metadata.get('inputonly') is True:
                continue

            field_name = self.field_name(build_type.field)
            description = build_type.metadata.get('description', '')
            mapped_type = self.map(build_type.source)
            if mapped_type:
                args = self.arguments(build_type.metadata.get('arguments'))
                if is_connection(source):
                    pagination_args = self.arguments(source.page_arguments())
                    if not args:
                        args = pagination_args
                    elif pagination_args:
                        args.update(pagination_args)
                result[field_name] = GraphQLField(mapped_type,
                                                  description=description,
                                                  args=args)
        return result

    def build_connection(self, source: Type[IConnection]) -> GraphQLFieldMap:
        result: GraphQLFieldMap = {}
        self.build_connection_interface()
        connection_class = getattr(source, '__origin__')
        wrapped = getattr(source, '__args__')[0]

        for build_type in self.build_type(connection_class):
            field_name = self.field_name(build_type.field)
            description = build_type.metadata.get('description', '')
            if is_sequence(build_type.source) and build_type.source.__args__[0] is IEdge[T]:
                inner = build_type.source.__args__[0]
                mapped_type: Optional[GraphQLOutputType] = self.build_connection_edge(inner.__origin__, wrapped)
            else:
                if issubclass(build_type.source, IPageInfo):
                    mapped_type = self.map_type(build_type.source,
                                                interfaces=(self.interfaces['IPageInfo'],))
                else:
                    mapped_type = self.map(build_type.source)
            if mapped_type:
                args = self.arguments(build_type.metadata.get('arguments'))
                result[field_name] = GraphQLField(mapped_type,
                                                  description=description,
                                                  args=args)
        return result

    def build_connection_edge(self, source: Type[IEdge], inner: Type[Any]) -> GraphQLNonNull[GraphQLObjectType]:
        fields: GraphQLFieldMap = {}
        name = self.type_name(inner)
        node_name = f'{name}Node'
        for build_type in self.build_type(source):
            field_name = self.field_name(build_type.field)
            description = build_type.metadata.get('description', '')
            if build_type.source is not INode[T]:
                mapped_type = self.map(build_type.source)
            else:
                mapped_type = self.map_type(inner, (self.interfaces['INode'],), node_name)
            if mapped_type:
                if is_required(build_type.field):
                    mapped_type = GraphQLNonNull(mapped_type)
                args = self.arguments(build_type.metadata.get('arguments'))
                fields[field_name] = GraphQLField(mapped_type,
                                                  description=description,
                                                  args=args)
        result = GraphQLNonNull(GraphQLObjectType(
            f'{name}Edge',
            fields=fields,
            interfaces=(self.interfaces['IEdge'],)))
        return result

    def build_connection_interface(self):
        breakpoint()
        if 'INode' not in self.types:
            self.interfaces['INode'] = GraphQLInterfaceType('INode', self.fields(INode))
        if 'IEdge' not in self.types:
            self.interfaces['IEdge'] = GraphQLInterfaceType('IEdge', self.fields(IEdge))
        if 'IPageInfo' not in self.types:
            self.interfaces['IPageInfo'] = GraphQLInterfaceType('IPageInfo', self.fields(IPageInfo))
        if 'IConnection' not in self.types:
            self.interfaces['IConnection'] = GraphQLInterfaceType('IConnection', self.fields(IConnection))
