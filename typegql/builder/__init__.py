from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, Field, is_dataclass, MISSING
from typing import Any, Dict, Generator, get_type_hints, Mapping, Optional, Type

import graphql
from graphql import (
    GraphQLEnumType,
    GraphQLFieldMap,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
)
from graphql.pyutils import snake_to_camel

from .types import ID, DateTime, Dictionary, Decimal, EnumType
from .utils import is_connection, is_enum, is_optional, is_sequence, load, to_snake

GraphQLEnumMap = Dict[str, GraphQLEnumType]
GraphQLObjectTypeMap = Dict[str, GraphQLObjectType]
GraphQLScalarMap = Mapping[str, GraphQLScalarType]


@dataclass
class BuildType:
    source: Type[Any]
    field: Field
    metadata: Mapping[str, Any]


class Helper:
    def __init__(self, source: Type[Any], builder: Builder):
        self.source = source
        self.builder = builder

    def fields(self) -> GraphQLFieldMap:
        return self.builder.fields(self.source)


class Builder(metaclass=ABCMeta):
    def __init__(self,
                 camelcase: bool = True):
        self.camelcase = camelcase
        self.scalars: GraphQLScalarMap = {
            'ID': ID(),
            'bool': graphql.GraphQLBoolean,
            'int': graphql.GraphQLInt,
            'float': graphql.GraphQLFloat,
            'str': graphql.GraphQLString,
            'datetime': DateTime(),
            'Dict': Dictionary(),
            'Decimal': Decimal(),
        }
        self.enums: GraphQLEnumMap = {}
        self.types: GraphQLObjectTypeMap = {}

    def field_name(self, field: Field) -> str:
        field_name = field.metadata.get('alias', field.name)
        if self.camelcase:
            field_name = snake_to_camel(field_name, upper=False)
        return field_name

    def type_name(self, source: Type[Any]) -> str:
        try:
            return source.__name__
        except AttributeError:
            if source._name:
                return source._name

        origin = source.__origin__
        return origin.__name__

    def type_description(self, source: Type[Any]) -> Optional[str]:
        return source.__doc__

    def map_scalar(self, source: Type[Any]) -> Optional[GraphQLScalarType]:
        name = self.type_name(source)
        return self.scalars.get(name)

    def map_enum(self, source: Type[Any]) -> Optional[GraphQLEnumType]:
        if not is_enum(source):
            return None
        name = self.type_name(source)
        if name in self.enums:
            return self.enums[name]
        enum_type = EnumType(name, source)
        self.enums[name] = enum_type
        return enum_type

    def map_sequence(self, source: Type[Any]) -> Optional[GraphQLList]:
        if not is_sequence(source):
            return None
        inner = self.map(source.__args__[0])
        if inner:
            return GraphQLList(inner)
        return None

    def map_type(self, source: Type[Any]) -> Optional[GraphQLObjectType]:
        name = self.type_name(source)
        if name in self.types:
            return self.types[name]
        description = self.type_description(source)
        helper = Helper(source, self)
        _type = graphql.GraphQLObjectType(name,
                                          description=description,
                                          fields=helper.fields)
        self.types[name] = _type
        return _type

    def map(self, source: Type[Any]) -> Optional[GraphQLOutputType]:
        print('wtf', source)
        if isinstance(source, graphql.GraphQLType):
            return source
        scalar = self.map_scalar(source)
        if scalar:
            return scalar
        enum = self.map_enum(source)
        if enum:
            return enum
        sequence = self.map_sequence(source)
        if sequence:
            return sequence

        _type = self.map_type(source)
        if _type:
            return _type
        return None

    def build_type(self, source: Type[Any]) -> Generator[BuildType, None, None]:
        if not is_dataclass(source):
            raise TypeError(f'Expected dataclass for {source}')

        hints = get_type_hints(source)
        for field in fields(source):
            metadata = field.metadata
            if field.name.startswith('_') or metadata.get('skip') is True:
                continue
            _type = hints.get(field.name, field.type)
            if is_optional(_type):
                _type = _type.__args__[0]

            yield BuildType(_type, field, metadata)

    @abstractmethod
    def fields(self, source: Type[Any]) -> GraphQLFieldMap:
        pass
