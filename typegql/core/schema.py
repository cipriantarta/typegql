import logging
from typing import Type, Callable, Any

from graphql import GraphQLSchema, GraphQLObjectType, graphql, OperationType, validate_schema
from graphql.pyutils import camel_to_snake

from typegql.core.graph import Graph

logger = logging.getLogger(__name__)


class Schema(GraphQLSchema):
    def __init__(self,
                 query: Type[Graph] = None,
                 mutation: Type[Graph] = None,
                 subscription: Type[Graph] = None,
                 camelcase=True):
        super().__init__()
        self.camelcase = camelcase

        if query:
            self.query: Callable = query
            query_fields = query.get_fields(query, camelcase=self.camelcase)
            query = GraphQLObjectType(
                'Query',
                fields=query_fields,
            )

        if mutation:
            self.mutation: Callable = mutation
            mutation_fields = mutation.get_fields(mutation, camelcase=self.camelcase)
            mutation = GraphQLObjectType(
                'Mutation',
                fields=mutation_fields
            )

        if subscription:
            self.subscription: Callable = subscription
            subscription_fields = subscription.get_fields(subscription, camelcase=self.camelcase)
            subscription = GraphQLObjectType(
                'Subscription',
                fields=subscription_fields
            )

        super().__init__(query, mutation, subscription)
        errors = validate_schema(self)
        if errors:
            raise errors[0]

    def _field_resolver(self, source, info, **kwargs):
        field_name = info.field_name
        if self.camelcase:
            snake_args = dict()
            keys = [k for k in kwargs.keys()]
            for key in keys:
                if key in info.parent_type.fields[field_name].args:
                    snake_args[camel_to_snake(key)] = kwargs.pop(key)
            field_name = camel_to_snake(field_name)
            kwargs.update(snake_args)

        if info.operation.operation == OperationType.MUTATION:
            try:
                mutation = getattr(source, f'mutate_{field_name}')
                return mutation(info, **kwargs)
            except AttributeError:
                return

        if Graph.is_graph(source.__class__):
            _type = source.__annotations__.get(field_name)
            if Graph.is_connection(_type):
                method = getattr(_type, 'resolve', None)
                if method:
                    return method(source, field_name, _type.__args__[0], info, **kwargs)
            elif Graph.is_graph(_type):
                return _type()

        value = (
            source.get(field_name)
            if isinstance(source, dict)
            else getattr(source, f'resolve_{field_name}', getattr(source, field_name, None))
        )
        if callable(value):
            return value(info, **kwargs)
        return value

    async def run(self, query: str, root: Graph = None, operation: str = None, context: Any = None, variables=None,
                  middleware=None):
        if query.startswith('mutation') and not root:
            root = self.mutation()
        elif not root:
            root = self.query()
        result = await graphql(self, query, root_value=root, field_resolver=self._field_resolver,
                               operation_name=operation,
                               context_value=context, variable_values=variables, middleware=middleware)
        return result
