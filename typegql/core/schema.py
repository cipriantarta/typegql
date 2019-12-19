import inspect
import logging
from dataclasses import is_dataclass
from inspect import isclass, isawaitable
from typing import Any, Callable, Dict, Optional, Type, cast

from graphql import (GraphQLField, GraphQLObjectType, GraphQLResolveInfo, GraphQLSchema, GraphQLType, OperationType,
                     graphql, parse, subscribe as gql_subscribe, validate_schema)
from graphql.execution import ExecutionContext, Middleware
from graphql.pyutils import camel_to_snake

from .builder import SchemaBuilder
from .execution import TGQLExecutionContext
from .pubsub import pubsub
from .utils import is_connection

logger = logging.getLogger(__name__)
ResolverType = Callable[[Any, GraphQLResolveInfo, Dict[str, Any]], Any]


class Schema(GraphQLSchema):
    def __init__(self,
                 query: Type = None,
                 mutation: Optional[Type] = None,
                 subscription: Optional[Type] = None,
                 types: Dict[str, GraphQLType] = None,
                 camelcase=True):
        super().__init__()
        self.camelcase = camelcase
        builder = SchemaBuilder(self.camelcase, types=types)
        query_gql, mutation_gql, subscription_gql = None, None, None
        if query:
            self.query = query
            query_fields = builder.get_fields(query)
            query_gql = GraphQLObjectType(
                'Query',
                fields=cast(Dict[str, GraphQLField], query_fields),
            )

        if mutation:
            self.mutation = mutation
            mutation_fields = builder.get_fields(mutation)
            mutation_gql = GraphQLObjectType(
                'Mutation',
                fields=cast(Dict[str, GraphQLField], mutation_fields)
            )

        if subscription:
            self.subscription = subscription
            subscription_fields = builder.get_fields(subscription)
            subscription_gql = GraphQLObjectType(
                'Subscription',
                fields=cast(Dict[str, GraphQLField], subscription_fields)
            )

        super().__init__(query_gql, mutation_gql, subscription_gql)
        errors = validate_schema(self)
        if errors:
            raise errors[0]

    def get_field_name(self, info: GraphQLResolveInfo):
        field_name = info.field_name
        if self.camelcase:
            field_name = camel_to_snake(field_name)
        return field_name

    def _field_resolver(self, source: Any, info: GraphQLResolveInfo, **kwargs):
        field_name = self.get_field_name(info)

        if info.operation.operation == OperationType.MUTATION and isclass(source.__class__):
            mutation = getattr(source, f'mutate_{field_name}', None)
            if mutation:
                return mutation(info, **kwargs)

        if is_dataclass(source.__class__):
            field = source.__dataclass_fields__.get(field_name)

            if is_connection(field.type):
                func = getattr(field.type, 'resolve', None)
                if func and inspect.ismethod(func):
                    return func(source, field_name, field.type.__args__[0], info, **kwargs)
                else:
                    logger.error(f'Expected {func} to be a method. Ignoring')

        value = (
            source.get(field_name)
            if isinstance(source, dict)
            else getattr(source, f'resolve_{field_name}', getattr(source, field_name, None))
        )
        if callable(value):
            return value(info, **kwargs)
        return value

    async def _subscription_field_resolver(self, source: Any, info: GraphQLResolveInfo, **kwargs):
        field_name = self.get_field_name(info)

        async for message in pubsub.subscribe(field_name):
            method = getattr(source, f'on_{field_name}', None)
            if not method:
                value = message
            else:
                value = method(message)
                if isawaitable(value):
                    value = await value
            yield {field_name: value}

    async def run(self, query: str,
                  root: Any = None,
                  resolver: ResolverType = None,
                  operation: str = None,
                  context: Any = None,
                  variables: Dict[str, Any] = None,
                  middleware: Middleware = None,
                  execution_context_class: Type[ExecutionContext] = TGQLExecutionContext):
        query = query.strip()
        if query.startswith('mutation') and not root:
            root = self.mutation()
        elif not root:
            root = self.query()
        result = await graphql(self,
                               query,
                               root_value=root,
                               field_resolver=resolver or self._field_resolver,
                               operation_name=operation,
                               context_value=context,
                               variable_values=variables,
                               middleware=middleware,
                               execution_context_class=execution_context_class)
        return result

    async def subscribe(self,
                        query: str,
                        root: Any = None,
                        subscription_resolver: ResolverType = None,
                        resolver: ResolverType = None,
                        operation: str = None,
                        context: Any = None,
                        variables: Dict[str, Any] = None):
        if not root:
            root = self.subscription()

        document = parse(query)
        result = await gql_subscribe(self,
                                     document,
                                     root,
                                     context,
                                     variables,
                                     operation,
                                     resolver or self._field_resolver,
                                     subscription_resolver or self._subscription_field_resolver)
        return result
