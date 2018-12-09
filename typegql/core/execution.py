from inspect import isawaitable
from typing import List, Any, Union, Dict

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
                self.convert_keys(arguments)
            result = resolve_fn(source, info, **arguments)
            if isawaitable(result):
                return self.await_result(result)
            return result
        except GraphQLError as e:
            return e


    def convert_keys(self, root: Dict) -> Dict:
        for key, value in root.items():
            if isinstance(value, dict):
                self.convert_keys(value)

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.convert_keys(item)

            root[camel_to_snake(key)] = root.pop(key)

