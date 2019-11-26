from typing import List, Any, Union

from graphql import (
    ExecutionContext,
    GraphQLField,
    FieldNode,
    GraphQLFieldResolver,
    GraphQLResolveInfo,
    GraphQLError,
    is_introspection_type
)
from graphql.execution.values import get_argument_values

from typegql.core.utils import to_snake


class TGQLExecutionContext(ExecutionContext):
    def resolve_field_value_or_error(
        self,
        field_def: GraphQLField,
        field_nodes: List[FieldNode],
        resolve_fn: GraphQLFieldResolver,
        source: Any,
        info: GraphQLResolveInfo
    ) -> Union[Exception, Any]:
        try:
            is_introspection = is_introspection_type(info.parent_type)
            camelcase = getattr(info.schema, 'camelcase', False)
            arguments = get_argument_values(field_def, field_nodes[0], self.variable_values)
            if camelcase and not is_introspection:
                arguments = to_snake(arguments=arguments)
            result = resolve_fn(source, info, **arguments)
            return result
        except GraphQLError as e:
            return e
        except Exception as e:
            return e
