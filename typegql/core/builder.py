from dataclasses import MISSING, fields, is_dataclass, Field
from functools import partial
from typing import Type, Any, Dict, get_type_hints, Union, Optional, List, cast

import graphql
from graphql import GraphQLInputField, GraphQLField, GraphQLType, GraphQLOutputType, GraphQLInterfaceType
from graphql.pyutils import snake_to_camel

from typegql.core.graph import GraphHelper
from .arguments import Argument, ArgumentList
from .connection import IConnection, INode, IEdge, IPageInfo, T
from .types import ID, DateTime, Dictionary, Decimal, EnumType
from .utils import is_enum, is_list, is_connection, to_snake, is_optional


class SchemaBuilder:
    def __init__(self, camelcase: bool, types: Dict = None):
        self.camelcase = camelcase
        self.types: Dict[str, Union[GraphQLType, GraphQLInterfaceType]] = {
            'ID': ID(),
            'bool': graphql.GraphQLBoolean,
            'int': graphql.GraphQLInt,
            'float': graphql.GraphQLFloat,
            'str': graphql.GraphQLString,
            'datetime': DateTime(),
            'Dict': Dictionary(),
            'Decimal': Decimal(),
        }
        if isinstance(types, Dict):
            self.types.update(types)

    def is_readonly(self, field: Field) -> bool:
        return field.metadata.get('readonly', False)

    def is_required(self, field: Field) -> bool:
        # TODO: remove ignore below after  https://github.com/python/mypy/issues/6910 gets fixed
        return all([field.default is MISSING,
                    field.default_factory is MISSING,  # type: ignore
                    not is_optional(field.type)])

    def get_fields(self, graph: Type[T], is_mutation=False) -> Dict[str, Union[GraphQLField, GraphQLInputField]]:
        result: Dict[str, Union[GraphQLField, GraphQLInputField]] = dict()
        hints = get_type_hints(graph)
        for field in fields(graph):
            if field.name.startswith('_'):
                continue
            _type = hints.get(field.name, field.type)
            if is_optional(_type):
                _type = _type.__args__[0]
            if is_mutation and self.is_readonly(field):
                continue

            graph_type = self.map_type(_type, is_mutation=is_mutation)
            if not graph_type:
                continue

            if self.is_required(field):
                graph_type = graphql.GraphQLNonNull(graph_type)
            args = self.arguments(field.metadata.get('arguments'), self.camelcase)
            if is_connection(_type) and not args:
                args = self.arguments(_type.page_arguments())

            field_name = field.metadata.get('alias', field.name)
            if self.camelcase:
                field_name = snake_to_camel(field_name, upper=False)

            description = field.metadata.get('description', '')
            if is_mutation:
                result[field_name] = GraphQLInputField(graph_type,
                                                       description=description, )
            else:
                result[field_name] = GraphQLField(graph_type,
                                                  description=description,
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
            origin = _type.__origin__
            if origin == Union and len(_type.__args__) == 2:
                return self.map_type(_type.__args__[0], is_mutation, interfaces)
            else:
                type_name = origin.__name__

        if is_connection(_type):
            return self.get_connection_type(_type)

        if is_enum(_type):
            if type_name in self.types:
                return self.types.get(type_name)
            enum_type = EnumType(type_name, _type)
            self.types[type_name] = enum_type
            return enum_type

        if is_list(_type):
            inner = self.map_type(_type.__args__[0], is_mutation=is_mutation)
            return graphql.GraphQLList(inner)

        if is_dataclass(_type):
            return self.build_object_type(type_name, _type, is_mutation=is_mutation, interfaces=interfaces)

        return self.types.get(type_name)

    def build_object_type(self, type_name, _type, is_mutation=False, interfaces=None):
        if is_mutation:
            type_name = f'{type_name}Input'
        if type_name in self.types:
            return self.types[type_name]

        graph_helper = GraphHelper(_type, self, is_mutation)
        if not is_mutation:
            graph_type = graphql.GraphQLObjectType(type_name,
                                                   description=_type.__doc__,
                                                   fields=graph_helper.get_fields,
                                                   interfaces=interfaces)
        else:
            load_method = getattr(_type, 'load', None)
            if load_method and self.camelcase:
                load_method = partial(to_snake, callback=load_method)
            elif self.camelcase:
                load_method = to_snake
            graph_type = graphql.GraphQLInputObjectType(type_name,
                                                        description=_type.__doc__,
                                                        fields=graph_helper.get_fields,
                                                        out_type=load_method)
        self.types[type_name] = graph_type
        return graph_type

    def arguments(self, definition: Optional[Dict], camelcase=True) -> Optional[graphql.GraphQLArgumentMap]:
        result: Optional[graphql.GraphQLArgumentMap] = dict()
        if not definition or not isinstance(definition, (list, tuple)):
            return None
        for arg in definition:
            if not isinstance(arg, (Argument, ArgumentList)):
                continue

            _type = self.map_type(arg.type, is_mutation=arg.is_input)
            if arg.required:
                _type = graphql.GraphQLNonNull(_type)
            arg_name = snake_to_camel(arg.name, False) if camelcase else arg.name
            result[arg_name] = graphql.GraphQLArgument(_type, description=arg.description)
        return result

    def get_connection_type(self, graph: Type[IConnection]) -> GraphQLType:
        self.build_connection_interface()
        connection_class = getattr(graph, '__origin__')
        wrapped = getattr(graph, '__args__')[0]

        connection_fields = dict()
        hints = get_type_hints(connection_class)
        for field in fields(connection_class):
            _type = hints.get(field.name, field.type)
            if is_optional(_type):
                _type = _type.__args__[0]

            graph_type: GraphQLOutputType  # mypy check
            if is_list(_type) and _type.__args__[0] is IEdge[T]:
                inner = _type.__args__[0]
                graph_type = graphql.GraphQLList(self.get_edge_field(inner.__origin__, wrapped))
            else:
                interfaces: List[GraphQLType] = []
                if issubclass(_type, IPageInfo):
                    interfaces = [self.types['IPageInfo']]
                graph_type = self.map_type(_type, interfaces=interfaces)
            if self.is_required(field):
                graph_type = graphql.GraphQLNonNull(graph_type)

            arguments = self.arguments(field.metadata.get('arguments'), self.camelcase)
            field_name = field.name
            if self.camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            connection_fields[field_name] = graphql.GraphQLField(graph_type,
                                                                 description=field.metadata.get('description'),
                                                                 args=arguments)

        type_name = f'{wrapped.__name__}Connection'
        if type_name in self.types:
            return self.types[type_name]
        result = graphql.GraphQLObjectType(type_name,
                                           fields=connection_fields,
                                           interfaces=(cast(GraphQLInterfaceType, self.types['IConnection']),))
        self.types[type_name] = result
        return result

    def get_edge_field(self, edge_type, inner: Type[T], camelcase=True):
        connection_fields = dict()
        hints = get_type_hints(edge_type)
        for field in fields(edge_type):
            _type = hints.get(field.name, field.type)
            if _type is INode[T]:
                graph_type = self.get_node_fields(inner)
            else:
                graph_type = self.map_type(_type)
            if self.is_required(field):
                graph_type = graphql.GraphQLNonNull(graph_type)
            field_name = field.name
            if camelcase:
                field_name = snake_to_camel(field_name, upper=False)
            connection_fields[field_name] = graph_type

        type_name = f'{inner.__name__}Edge'
        if type_name in self.types:
            return self.types.get(type_name)
        result = graphql.GraphQLNonNull(graphql.GraphQLObjectType(
            f'{inner.__name__}Edge',
            fields=connection_fields,
            interfaces=(cast(GraphQLInterfaceType, self.types['IEdge']),)
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
            fields=cast(Dict[str, GraphQLField], self.get_fields(_type)),
            interfaces=(cast(GraphQLInterfaceType, self.types.get('INode')),)
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
