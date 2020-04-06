from typing import Any, Optional, Type

from graphql import (
    GraphQLField,
    GraphQLFieldMap,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
)

from .base import BuilderBase, GraphQLObjectTypeMap
from .connection import IConnection, IEdge, INode, IPageInfo, T
from .utils import is_connection, is_required, is_sequence


class QueryBuilder(BuilderBase):
    def __init__(self, types: Optional[GraphQLObjectTypeMap] = None):
        self.query_types = types or {}

    def query_fields(self, source: Type[Any]) -> GraphQLFieldMap:
        result: GraphQLFieldMap = {}

        for build_type in self.build_type(source):
            if build_type.metadata.get("inputonly") is True:
                continue

            field_name = self.field_name(build_type.field)
            description = build_type.metadata.get("description", "")
            if not is_connection(build_type.source):
                mapped_type = self.map_output(build_type.source)
            else:
                mapped_type = self.build_connection(build_type.source)
            if mapped_type:
                args = self.arguments(build_type.metadata.get("arguments"))
                if is_connection(build_type.source):
                    pagination_args = self.arguments(build_type.source.page_arguments())
                    if not args:
                        args = pagination_args
                    elif pagination_args:
                        args.update(pagination_args)

                if is_required(build_type.field):
                    mapped_type = GraphQLNonNull(mapped_type)
                result[field_name] = GraphQLField(
                    mapped_type, description=description, args=args
                )
        return result

    def build_connection(self, source: Type[Any]) -> GraphQLObjectType:
        fields: GraphQLFieldMap = {}
        self.build_connection_interface()
        connection_class = getattr(source, "__origin__")
        wrapped = getattr(source, "__args__")[0]

        for build_type in self.build_type(connection_class):
            field_name = self.field_name(build_type.field)
            description = build_type.metadata.get("description", "")
            if (
                is_sequence(build_type.source)
                and build_type.source.__args__[0] is IEdge[T]
            ):
                inner = build_type.source.__args__[0]
                mapped_type: Optional[GraphQLOutputType] = self.build_connection_edge(
                    inner.__origin__, wrapped
                )
                mapped_type = GraphQLList(mapped_type)
            else:
                if issubclass(build_type.source, IPageInfo):
                    mapped_type = self.map_type(
                        build_type.source, interfaces=(self.interfaces["IPageInfo"],)
                    )
                else:
                    mapped_type = self.map_output(build_type.source)
            if mapped_type:
                args = self.arguments(build_type.metadata.get("arguments"))
                if is_required(build_type.field):
                    mapped_type = GraphQLNonNull(mapped_type)
                fields[field_name] = GraphQLField(
                    mapped_type, description=description, args=args
                )
        name = self.type_name(wrapped)
        connection_name = f"{name}Connection"
        if connection_name in self.query_types:
            return self.query_types[connection_name]
        result = GraphQLObjectType(
            connection_name,
            description=f"{name} relay connection",
            fields=fields,
            interfaces=(self.interfaces["IConnection"],),
        )
        self.query_types[connection_name] = result
        return result

    def build_connection_edge(
        self, source: Type[IEdge], inner: Type[Any]
    ) -> GraphQLObjectType:
        fields: GraphQLFieldMap = {}
        name = self.type_name(inner)
        node_name = f"{name}Node"
        for build_type in self.build_type(source):
            field_name = self.field_name(build_type.field)
            description = build_type.metadata.get("description", "")
            if build_type.source is not INode[T]:
                mapped_type = self.map_output(build_type.source)
            else:
                mapped_type = self.map_type(
                    inner, (self.interfaces["INode"],), node_name
                )
            if mapped_type:
                if is_required(build_type.field):
                    mapped_type = GraphQLNonNull(mapped_type)
                args = self.arguments(build_type.metadata.get("arguments"))
                fields[field_name] = GraphQLField(
                    mapped_type, description=description, args=args
                )
        result = GraphQLObjectType(
            f"{name}Edge", fields=fields, interfaces=(self.interfaces["IEdge"],)
        )
        return result

    def build_connection_interface(self):
        if "INode" not in self.interfaces:
            self.interfaces["INode"] = GraphQLInterfaceType(
                "INode",
                self.query_fields(INode),
                description=self.type_description(INode),
            )
        if "IEdge" not in self.interfaces:
            self.interfaces["IEdge"] = GraphQLInterfaceType(
                "IEdge",
                self.query_fields(IEdge),
                description=self.type_description(IEdge),
            )
        if "IPageInfo" not in self.interfaces:
            self.interfaces["IPageInfo"] = GraphQLInterfaceType(
                "IPageInfo",
                self.query_fields(IPageInfo),
                description=self.type_description(IPageInfo),
            )
        if "IConnection" not in self.interfaces:
            self.interfaces["IConnection"] = GraphQLInterfaceType(
                "IConnection",
                self.query_fields(IConnection),
                description=self.type_description(IConnection),
            )
