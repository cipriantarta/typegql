from inspect import isawaitable
from typing import List, Any, Union

from graphql import ExecutionContext, GraphQLField, FieldNode, GraphQLFieldResolver, GraphQLResolveInfo, GraphQLError, \
    GraphQLSchema, is_introspection_type
from graphql.execution.values import get_argument_values
from graphql.pyutils import camel_to_snake


class TGQLExecutionContext(ExecutionContext):
    async def await_result(self, result):
        return await result

    def resolve_field_value_or_error(
        self,
        field_def: GraphQLField,
        field_nodes: List[FieldNode],
        resolve_fn: GraphQLFieldResolver,
        source: Any,
        info: GraphQLResolveInfo
    ) -> Union[Exception, Any]:
        try:
            camelcase = getattr(info.schema, 'camelcase', False)
            arguments = get_argument_values(field_def, field_nodes[0], self.variable_values)
            if camelcase and not is_introspection_type(info.parent_type):
                keys = [k for k in arguments.keys()]
                for key in keys:
                    if key in info.parent_type.fields[info.field_name].args:
                        arguments[camel_to_snake(key)] = arguments.pop(key)
            result = resolve_fn(source, info, **arguments)
            if isawaitable(result):
                return self.await_result(result)
            return result
        except GraphQLError as e:
            return e
