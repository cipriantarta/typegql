from typing import get_type_hints, Type, Any, Dict

import graphql
from graphql.pyutils import snake_to_camel

from typegql import Graph
from typegql.core.graph import GraphHelper
from .arguments import Argument, ArgumentList
from .connection import IConnection, INode, IEdge, IPageInfo, T
from .fields import Field
from .types import DateTime, Dictionary
from .utils import is_enum, is_list, is_graph, is_connection


class SchemaBuilder:
    def __init__(self, camelcase: bool, types: Dict = None):
        self.camelcase = camelcase
        self.types = {
            'ID': graphql.GraphQLID,
            'bool': graphql.GraphQLBoolean,
            'int': graphql.GraphQLInt,
            'float': graphql.GraphQLFloat,
            'str': graphql.GraphQLString,
            'datetime': DateTime(),
            'Dict': Dictionary(),
            'Decimal': graphql.GraphQLFloat
        }
        if isinstance(types, Dict):
            self.types.update(types)

    def get_fields(self, graph: Type[Any], is_mutation=False):
        result = dict()
        for name, _type in get_type_hints(graph).items():
            field = getattr(graph, name, None)

            if not isinstance(field, Field):
                continue

            if is_mutation and not field.mutation:
                continue

            graph_type = self.map_type(_type, is_mutation=is_mutation)
            if not graph_type:
                continue

            if field.required:
                graph_type = graphql.GraphQLNonNull(graph_type)
            if is_connection(_type):
                field.arguments.extend(_type.page_arguments())

            args = self.arguments(field, self.camelcase)
            field_name = field.name or name
            if self.camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            if is_mutation:
                result[field_name] = graphql.GraphQLInputField(graph_type, description=field.description)
            else:
                result[field_name] = graphql.GraphQLField(graph_type,
                                                          description=field.description,
                                                          args=args)

        return result

    def map_type(self, _type: Any, is_mutation=False, interfaces=None):
        if isinstance(_type, graphql.GraphQLType):
            return _type
        try:
            type_name = _type.__name__
        except AttributeError:
            type_name = _type._name

        if not type_name:
            type_name = _type.__origin__.__name__

        if is_connection(_type):
            return self.get_connection_fields(_type)

        if is_enum(_type):
            if type_name in self.types:
                return self.types.get(type_name)
            enum_type = graphql.GraphQLEnumType(type_name, _type)
            self.types[type_name] = enum_type
            return enum_type

        if is_list(_type):
            inner = self.map_type(_type.__args__[0], is_mutation=is_mutation)
            return graphql.GraphQLList(inner)

        if is_graph(_type):
            return self.build_object_type(type_name, _type, is_mutation=is_mutation, interfaces=interfaces)

        return self.types.get(type_name)

    def get_fields_lazy(self):
        return dict()

    def build_object_type(self, type_name, _type, is_mutation=False, interfaces=None):
        if is_mutation:
            type_name = f'{type_name}Mutation'
        if type_name in self.types:
            return self.types[type_name]

        graph_helper = GraphHelper(_type, self, is_mutation)
        fields = graph_helper.get_fields
        if not is_mutation:
            graph_type = graphql.GraphQLObjectType(type_name,
                                                   description=_type.__doc__,
                                                   fields=fields,
                                                   interfaces=interfaces)
        else:
            graph_type = graphql.GraphQLInputObjectType(type_name,
                                                        description=_type.__doc__,
                                                        fields=fields)
        self.types[type_name] = graph_type
        return graph_type

    def arguments(self, field: Field, camelcase=True):
        result: graphql.GraphQLArgumentMap = dict()
        arguments = field.arguments
        if not isinstance(arguments, (list, tuple)):
            return
        for arg in arguments:
            if not isinstance(arg, (Argument, ArgumentList)):
                continue

            _type = self.map_type(arg.type, is_mutation=arg.is_input)
            if arg.required:
                _type = graphql.GraphQLNonNull(_type)
            arg_name = snake_to_camel(arg.name, False) if camelcase else arg.name
            result[arg_name] = graphql.GraphQLArgument(_type, description=arg.description)
        return result

    def get_connection_fields(self, graph: Type[IConnection]):
        if not is_connection(graph):
            return self.get_fields(graph)

        self.build_connection_interface()
        connection_class = graph.__origin__
        wrapped = graph.__args__[0]

        fields = {}
        for name, _type in get_type_hints(connection_class).items():
            field = getattr(graph, name, None)
            if not isinstance(field, Field):
                continue

            if is_list(_type) and _type.__args__[0] is IEdge[T]:
                inner = _type.__args__[0]
                graph_type = graphql.GraphQLList(self.get_edge_field(inner.__origin__, wrapped))
            else:
                interfaces = []
                if issubclass(_type, IPageInfo):
                    interfaces = [self.types.get('IPageInfo')]
                graph_type = self.map_type(_type, interfaces=interfaces)
            if field.required:
                graph_type = graphql.GraphQLNonNull(graph_type)

            arguments = self.arguments(field, self.camelcase)
            field_name = field.name or name
            if self.camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            fields[field_name] = graphql.GraphQLField(graph_type, description=field.description, args=arguments)

        type_name = f'{wrapped.__name__}Connection'
        if type_name in self.types:
            return self.types.get(type_name)
        result = graphql.GraphQLObjectType(type_name,
                                           fields=fields,
                                           interfaces=(self.types.get('IConnection'),))
        self.types[type_name] = result
        return result

    def get_edge_field(self, edge_type, inner: Type[T], camelcase=True):
        fields = dict()
        for name, _type in get_type_hints(edge_type).items():
            field = getattr(edge_type, name, None)
            if not isinstance(field, Field):
                continue
            if _type is INode[T]:
                graph_type = self.get_node_fields(inner)
            else:
                graph_type = self.map_type(_type)
            if field.required:
                graph_type = graphql.GraphQLNonNull(graph_type)
            field_name = field.name or name
            if camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            fields[field_name] = graph_type

        type_name = f'{inner.__name__}Edge'
        if type_name in self.types:
            return self.types.get(type_name)
        result = graphql.GraphQLNonNull(graphql.GraphQLObjectType(
            f'{inner.__name__}Edge',
            fields=fields,
            interfaces=(self.types.get('IEdge'),)
        ))
        self.types[type_name] = result
        return result

    def get_node_fields(self, _type: Type[T]):
        type_name = f'{_type.__name__}Node'
        if type_name in self.types:
            return self.types.get(type_name)
        result = graphql.GraphQLObjectType(
            type_name,
            description=_type.__doc__,
            fields=self.get_fields(_type),
            interfaces=(self.types.get('INode'),)
        )
        self.types[type_name] = result
        return result

    def build_connection_interface(self):
        if 'INode' not in self.types:
            self.types['INode'] = graphql.GraphQLInterfaceType('INode', self.get_fields(INode))
        if 'IEdge' not in self.types:
            self.types['IEdge'] = graphql.GraphQLInterfaceType('IEdge', self.get_fields(IEdge))
        if 'IPageInfo' not in self.types:
            self.types['IPageInfo'] = graphql.GraphQLInterfaceType('IPageInfo', self.get_fields(IPageInfo))
        if 'IConnection' not in self.types:
            self.types['IConnection'] = graphql.GraphQLInterfaceType('IConnection', self.get_fields(IConnection))
