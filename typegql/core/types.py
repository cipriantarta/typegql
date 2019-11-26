import ast
import base64
from datetime import datetime
from decimal import Decimal as DecimalType
from enum import Enum
from typing import Dict, Any, Union, Type

import graphql
from graphql import ValueNode, GraphQLEnumType, GraphQLEnumValue
from graphql.error import InvalidType
from graphql.language import ast as graphql_ast


class ID(graphql.GraphQLScalarType):
    def __init__(self):
        super().__init__(
            name='ID',
            description="The `ID` scalar type represents a unique identifier,"
                        " often used to refetch an object or as key for a cache."
                        " The ID type appears in a JSON response as a String; however,"
                        " it is not intended to be human-readable. When expected as an"
                        ' input type, any string (such as `"4"`) or integer (such as'
                        " `4`) input value will be accepted as an ID.",
            serialize=self.serialize,
            parse_value=self.parse_value,
            parse_literal=self.parse_literal,
        )

    @staticmethod
    def serialize(value: Any) -> Any:
        if not isinstance(value, str):
            value = str(value)
        return base64.b64encode(value.encode()).decode()

    def parse_literal(self, node: ValueNode, _variables: Dict[str, Any] = None):
        if isinstance(node, graphql_ast.StringValueNode):
            try:
                return base64.b64decode(node.value).decode()
            except ValueError:
                return InvalidType()
        return super().parse_literal(node, _variables)

    @staticmethod
    def parse_value(value: Any) -> Any:
        try:
            return base64.b64decode(value).decode()
        except ValueError:
            return InvalidType()

    @classmethod
    def decode(cls, value):
        return base64.b64decode(value).decode()


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
        if not isinstance(value, datetime):
            return InvalidType('datetime value expected')
        return value.isoformat()

    def parse_literal(self, node: ValueNode, _variables: Dict[str, Any] = None):
        if isinstance(node, graphql_ast.StringValueNode):
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


class Dictionary(graphql.GraphQLScalarType):
    def __init__(self, name='Dictionary'):
        super().__init__(
            name=name,
            description='The`Dictionary` type is a KV mapping type',
            serialize=self.serialize,
            parse_value=self.parse_value,
            parse_literal=self.parse_literal,
        )

    @staticmethod
    def serialize(value: Any) -> Any:
        if not isinstance(value, dict):
            return InvalidType('Dictionary value expected')
        return value

    def parse_literal(self, node: ValueNode, _variables: Dict[str, Any] = None):
        if isinstance(node, graphql_ast.StringValueNode):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                pass

    @staticmethod
    def parse_value(value: Any) -> Any:
        try:
            return ast.literal_eval(value)
        except ValueError:
            pass


class Decimal(graphql.GraphQLScalarType):
    def __init__(self, name='Decimal'):
        super().__init__(
            name=name,
            description='Floating point class for decimal arithmetic.',
            serialize=self.serialize,
            parse_value=self.parse_value,
            parse_literal=self.parse_literal,
        )

    @staticmethod
    def serialize(value: Any) -> Any:
        if not isinstance(value, (DecimalType, int, float)):
            return InvalidType('Decimal value expected')
        return value

    def parse_literal(self, node: ValueNode, _variables: Dict[str, Any] = None):
        if isinstance(node, graphql_ast.FloatValueNode):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                pass

    @staticmethod
    def parse_value(value: Any) -> Any:
        try:
            return ast.literal_eval(value)
        except ValueError:
            pass


class EnumValue(GraphQLEnumValue):
    def __init__(self, value, **kwargs):
        super().__init__(value, **kwargs)
        self._type = value

    def __getattribute__(self, item):
        if item == 'value':
            return self._type
        return super().__getattribute__(item)


class EnumType(GraphQLEnumType):
    def __init__(self, name, _type: Type[Enum]):
        super().__init__(
            name=name,
            values={name: EnumValue(value) for name, value in _type.__members__.items()},
            description=str(_type.__doc__))

    def serialize(self, value: Any) -> Union[str, None, InvalidType]:
        if not isinstance(value, Enum):
            return InvalidType('Enum value expected')
        return value.value
