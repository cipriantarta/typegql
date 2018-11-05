import logging
from typing import Type, Callable

from graphql import GraphQLSchema, GraphQLObjectType, graphql, OperationType

from typegql.core.graph import Graph

logger = logging.getLogger(__name__)


def _field_resolver(source, info, **kwargs):
    field_name = info.field_name

    if info.operation.operation == OperationType.MUTATION:
        try:
            mutation = getattr(source, f'mutate_{field_name}')
            return mutation(info, **kwargs)
        except AttributeError:
            return

    value = (
        source.get(field_name)
        if isinstance(source, dict)
        else getattr(source, f'resolve_{field_name}', getattr(source, field_name, None))
    )
    if callable(value):
        return value(info, **kwargs)
    return value


class Schema(GraphQLSchema):
    def __init__(self,
                 query: Type[Graph] = None,
                 mutation: Type[Graph] = None,
                 subscription: Type[Graph] = None):
        super().__init__()

        if query:
            self.query: Callable = query
            query_fields = query.get_fields(query)
            query = GraphQLObjectType(
                'Query',
                fields=query_fields,
            )

        if mutation:
            self.mutation: Callable = mutation
            mutation_fields = mutation.get_fields(mutation)
            mutation = GraphQLObjectType(
                'Mutation',
                fields=mutation_fields
            )

        if subscription:
            self.subscription: Callable = subscription
            subscription_fields = subscription.get_fields(subscription)
            subscription = GraphQLObjectType(
                'Subscription',
                fields=subscription_fields
            )

        super().__init__(query, mutation, subscription)

    async def run(self, query: str, root: Graph = None):
        if query.startswith('mutation') and not root:
            root = self.mutation()
        elif not root:
            root = self.query()
        result = await graphql(self, query, root_value=root, field_resolver=_field_resolver)
        return result
