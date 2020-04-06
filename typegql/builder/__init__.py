from __future__ import annotations

from typing import Optional

from .base import BuilderBase, GraphQLEnumMap, GraphQLInterfaceMap, GraphQLScalarMap
from .mutation import GraphQLInputObjectTypeMap, MutationBuilder
from .query import GraphQLObjectTypeMap, QueryBuilder


class Builder(QueryBuilder, MutationBuilder):
    def __init__(
        self,
        camelcase: bool = True,
        scalars: Optional[GraphQLScalarMap] = None,
        enums: Optional[GraphQLEnumMap] = None,
        interfaces: Optional[GraphQLInterfaceMap] = None,
        query_types: Optional[GraphQLObjectTypeMap] = None,
        mutation_types: Optional[GraphQLInputObjectTypeMap] = None,
    ):
        BuilderBase.__init__(self, camelcase, scalars, enums, interfaces)
        QueryBuilder.__init__(self, types=query_types)
        MutationBuilder.__init__(self, types=mutation_types)
