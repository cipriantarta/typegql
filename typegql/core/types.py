import ast

import base64
from datetime import datetime
from typing import Dict

import graphql
from graphql.error import InvalidType
from graphql.language import ast as graphql_ast


class DateTime(graphql.GraphQLScalarType):
    def __init__(self, name='DateTime'):
        super().__init__(
            name=name,
            description='The `DateTime` scalar type represents a DateTime value as specified by '
                        '[iso8601](https://en.wikipedia.org/wiki/ISO_8601).',
            serialize=DateTime.serialize,
            parse_value=DateTime.parse_value,
            parse_literal=DateTime.parse_literal,
        )

    @staticmethod
    def serialize(value: datetime):
        assert isinstance(value, datetime), 'datetime value expected'
        return value.isoformat()

    @staticmethod
    def parse_literal(node):
        if isinstance(node, graphql_ast.StringValueNode):
            try:
                return datetime.fromisoformat(node.value)
            except ValueError:
                return InvalidType()

    @staticmethod
    def parse_value(value: str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return InvalidType()


class ID(graphql.GraphQLScalarType):
    @classmethod
    def encode(cls, value):
        if not isinstance(value, str):
            value = str(value)
        return base64.b64encode(value.encode()).decode()

    @classmethod
    def decode(cls, value):
        return base64.b64decode(value).decode()


class Dictionary(graphql.GraphQLScalarType):
    def __init__(self, name='Dictionary'):
        super().__init__(
            name=name,
            description='Dictionary type / HashMap',
            serialize=Dictionary.serialize,
            parse_value=Dictionary.parse_value,
            parse_literal=Dictionary.parse_literal,
        )

    @staticmethod
    def serialize(value: Dict):
        assert isinstance(value, dict), 'dict value expected'
        return value

    @staticmethod
    def parse_literal(node):
        if isinstance(node, graphql_ast.StringValueNode):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return InvalidType()

    @staticmethod
    def parse_value(value: str):
        try:
            return ast.literal_eval(value)
        except ValueError:
            return InvalidType()
