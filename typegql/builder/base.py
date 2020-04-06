from __future__ import annotations

from abc import ABCMeta
from dataclasses import Field, dataclass, fields, is_dataclass
from functools import partial
from typing import (
    Any,
    Dict,
    Generator,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    get_type_hints,
)

import graphql
from graphql import (
    GraphQLArgumentMap,
    GraphQLEnumType,
    GraphQLFieldMap,
    GraphQLInputFieldMap,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLWrappingType,
)
from graphql.pyutils import snake_to_camel

from .arguments import Argument, ArgumentList
from .types import (
    EnumType,
    GraphQLDateTime,
    GraphQLDecimal,
    GraphQLDictionary,
    GraphQLID,
)
from .utils import is_enum, is_optional, is_sequence, load, to_snake

GraphQLEnumMap = Dict[str, GraphQLEnumType]
GraphQLInputObjectTypeMap = Dict[str, GraphQLInputObjectType]
GraphQLInterfaceMap = Dict[str, GraphQLInterfaceType]
GraphQLIntersection = Union[
    GraphQLScalarType, GraphQLEnumType, GraphQLWrappingType, None
]
GraphQLObjectTypeMap = Dict[str, GraphQLObjectType]
GraphQLScalarMap = Mapping[str, GraphQLScalarType]


@dataclass
class BuildType:
    source: Type[Any]
    field: Field
    metadata: Mapping[str, Any]


class Helper:
    def __init__(self, source: Type[Any], builder: BuilderBase):
        self.source = source
        self.builder = builder

    def query_fields(self) -> GraphQLFieldMap:
        return self.builder.query_fields(self.source)

    def input_fields(self) -> GraphQLInputFieldMap:
        return self.builder.input_fields(self.source)


class BuilderBase(metaclass=ABCMeta):
    def __init__(
        self,
        camelcase: bool = True,
        scalars: Optional[GraphQLScalarMap] = None,
        enums: Optional[GraphQLEnumMap] = None,
        interfaces: Optional[GraphQLInterfaceMap] = None,
    ):
        self.camelcase = camelcase
        self.scalars: GraphQLScalarMap
        default_scalars = {
            "ID": GraphQLID,
            "bool": graphql.GraphQLBoolean,
            "int": graphql.GraphQLInt,
            "float": graphql.GraphQLFloat,
            "str": graphql.GraphQLString,
            "datetime": GraphQLDateTime,
            "Dict": GraphQLDictionary,
            "Decimal": GraphQLDecimal,
        }
        if scalars:
            default_scalars.update(scalars)
        self.scalars = default_scalars
        self.enums: GraphQLEnumMap = enums or {}
        self.interfaces = interfaces or {}

        # These are foor mypy only
        self.query_types: GraphQLObjectTypeMap = {}
        self.mutation_types: GraphQLInputObjectTypeMap = {}

    def arguments(self, definition: Optional[Dict]) -> Optional[GraphQLArgumentMap]:
        result: GraphQLArgumentMap = dict()
        if not definition or not isinstance(definition, (list, tuple)):
            return None
        for arg in definition:
            if not isinstance(arg, (Argument, ArgumentList)):
                continue

            mapped_type = self.map_input(arg.type)
            if arg.required:
                mapped_type = graphql.GraphQLNonNull(mapped_type)
            arg_name = snake_to_camel(arg.name, False) if self.camelcase else arg.name
            result[arg_name] = graphql.GraphQLArgument(
                mapped_type, description=arg.description
            )
        return result

    def field_name(self, field: Field) -> str:
        field_name = field.metadata.get("alias", field.name)
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

    def map_sequence(
        self, source: Type[Any], is_input: bool = False
    ) -> Optional[GraphQLList]:
        if not is_sequence(source):
            return None

        inner: GraphQLType
        if is_input:
            inner = self.map_input(source.__args__[0])
        else:
            inner = self.map_output(source.__args__[0])
        if inner:
            return GraphQLList(inner)
        return None

    def map_type(
        self,
        source: Type[Any],
        interfaces: Optional[Sequence[GraphQLInterfaceType]] = None,
        alias: Optional[str] = None,
    ) -> GraphQLObjectType:
        name = alias or self.type_name(source)
        if name in self.query_types:
            return self.query_types[name]
        description = self.type_description(source)
        helper = Helper(source, self)
        _type = graphql.GraphQLObjectType(
            name,
            description=description,
            fields=helper.query_fields,
            interfaces=interfaces,
        )
        self.query_types[name] = _type
        return _type

    def map_intersection(
        self, source: Type[Any], is_input: bool = False
    ) -> GraphQLIntersection:
        scalar = self.map_scalar(source)
        if scalar:
            return scalar
        enum = self.map_enum(source)
        if enum:
            return enum
        sequence = self.map_sequence(source, is_input)
        if sequence:
            return sequence
        return None

    def map_output(
        self,
        source: Type[Any],
        interfaces: Optional[Sequence[GraphQLInterfaceType]] = None,
        alias: Optional[str] = None,
    ) -> GraphQLOutputType:

        intersection = self.map_intersection(source)
        if intersection:
            return intersection

        name = alias or self.type_name(source)
        if name in self.interfaces:
            return self.interfaces[name]

        return self.map_type(source, interfaces, alias)

    def map_input(self, source: Type[Any]) -> GraphQLInputType:
        intersection = self.map_intersection(source, True)
        if intersection:
            return intersection

        name = f"{self.type_name(source)}Input"
        if name in self.mutation_types:
            return self.mutation_types[name]

        load_method = getattr(source, "load", None)
        if load_method:
            load_method = partial(load, callback=load_method, camelcase=self.camelcase)
        elif self.camelcase:
            load_method = to_snake

        helper = Helper(source, self)
        result = graphql.GraphQLInputObjectType(
            name,
            description=source.__doc__,
            fields=helper.input_fields,
            out_type=load_method,
        )
        self.mutation_types[name] = result
        return result

    def build_type(self, source: Type[Any]) -> Generator[BuildType, None, None]:
        if not is_dataclass(source):
            raise TypeError(f"Expected dataclass for {source}")

        hints = get_type_hints(source)
        for field in fields(source):
            metadata = field.metadata
            if field.name.startswith("_") or metadata.get("skip") is True:
                continue
            _type = hints.get(field.name, field.type)
            if is_optional(_type):
                _type = _type.__args__[0]

            yield BuildType(_type, field, metadata)

    def query_fields(self, source: Type[Any]) -> GraphQLFieldMap:
        pass

    def input_fields(self, source: Type[Any]) -> GraphQLInputFieldMap:
        pass
