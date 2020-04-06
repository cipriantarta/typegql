from typing import Any, Dict, Optional, Type

from graphql import (
    GraphQLInputField,
    GraphQLInputFieldMap,
    GraphQLInputType,
    GraphQLNonNull,
)

from .base import BuilderBase, GraphQLInputObjectTypeMap
from .utils import is_required

GraphQLInputTypeMap = Dict[str, GraphQLInputType]


class MutationBuilder(BuilderBase):
    def __init__(self, types: Optional[GraphQLInputObjectTypeMap] = None):
        self.mutation_types = types or {}

    def input_fields(self, source: Type[Any]) -> GraphQLInputFieldMap:
        result: GraphQLInputFieldMap = {}

        for build_type in self.build_type(source):
            if build_type.metadata.get("readonly") is True:
                continue

            field_name = self.field_name(build_type.field)
            description = build_type.metadata.get("description", "")
            mapped_type = self.map_input(build_type.source)

            if is_required(build_type.field):
                mapped_type = GraphQLNonNull(mapped_type)
            result[field_name] = GraphQLInputField(mapped_type, description=description)
        return result
