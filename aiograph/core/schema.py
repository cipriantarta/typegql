from enum import Enum
from typing import Type

from graphql import GraphQLSchema, GraphQLObjectType, graphql

from aiograph.core.graph import Graph, Connection


class Operation(Enum):
    QUERY = 'query'
    MUTATION = 'mutation'
    SUBSCRIPTION = 'subscription'


def _field_resolver(source, info, **args):
    field_name = info.field_name
    value = (
        source.get(field_name)
        if isinstance(source, dict)
        else getattr(source, f'resolve_{field_name}', getattr(source, field_name, None))
    )
    if callable(value):
        return value(info, **args)
    return value


class Schema(GraphQLSchema):
    def __init__(self,
                 query: Type[Graph] = None,
                 mutation: Type[Graph] = None,
                 subscription: Type[Graph] = None):
        super().__init__()

        if query:
            query_fields = Graph.get_fields(query)
            self.query_type = GraphQLObjectType(
                'Query',
                fields=query_fields,
            )
            self.root = query()

        if mutation:
            mutation_fields = Graph.get_fields(mutation)
            self.mutation_type = GraphQLObjectType(
                'Mutation',
                fields=mutation_fields
            )

        if subscription:
            subscription_fields = Graph.get_fields(subscription)
            self.subscription_type = GraphQLObjectType(
                'Subscription',
                fields=subscription_fields
            )

    async def run(self, query, root: Graph = None):
        root = root or self.root
        return await graphql(self, query, root_value=root, field_resolver=_field_resolver)
