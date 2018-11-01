import base64
from datetime import datetime

import graphql
from graphql.language import ast


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
        if isinstance(node, ast.StringValueNode):
            try:
                return datetime.fromisoformat(node.value)
            except ValueError:
                pass

    @staticmethod
    def parse_value(value: str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass


class ID(graphql.GraphQLScalarType):
    @classmethod
    def encode(cls, value):
        if not isinstance(value, str):
            value = str(value)
        return base64.b64encode(value.encode()).decode()

    @classmethod
    def decode(cls, value):
        return base64.b64decode(value).decode()
