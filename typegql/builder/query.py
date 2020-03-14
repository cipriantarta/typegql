from typing import Any, Dict, Optional, Type

from graphql import GraphQLArgumentMap, GraphQLField, GraphQLFieldMap, GraphQLOutputType

from . import Builder
from .utils import is_connection

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
        for build_type in self.build_type(source):
            if is_connection(build_type.source):
                print('ASDA')
                continue
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
