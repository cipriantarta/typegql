from dataclasses import MISSING, Field
from enum import Enum
from typing import Any, Callable, Dict, List, MutableSequence, Sequence, Union

from graphql.pyutils import camel_to_snake

from .connection import IConnection


def is_sequence(_type: Any) -> bool:
    try:
        return issubclass(_type.__origin__, (List, MutableSequence, Sequence))
    except AttributeError:
        return False


def is_enum(_type: Any) -> bool:
    try:
        return issubclass(_type, Enum)
    except TypeError:
        return False


def is_connection(_type: Any) -> bool:
    try:
        return _type.__origin__ is IConnection or issubclass(
            _type.__origin__, IConnection
        )
    except (TypeError, AttributeError):
        return False


def is_optional(_type: Any) -> bool:
    if hasattr(_type, "__origin__") and _type.__origin__ == Union:
        if len(_type.__args__) == 2 and isinstance(None, _type.__args__[1]):
            return True
    return False


def is_readonly(field: Field) -> bool:
    return field.metadata.get("readonly", False)


def is_inputonly(field: Field) -> bool:
    return field.metadata.get("inputonly", False)


def is_required(field: Field) -> bool:
    return all(
        [
            field.default is MISSING,
            field.default_factory is MISSING,  # type: ignore
            not is_optional(field.type),
        ]
    )


def to_snake(arguments: Dict) -> Dict[str, Any]:
    if not isinstance(arguments, dict) or not arguments:
        return arguments
    result = dict()
    for key, value in arguments.items():
        camel = camel_to_snake(key)
        if isinstance(value, list):
            for arg in value:
                result[camel] = to_snake(arg)
        elif isinstance(value, dict):
            result[camel] = to_snake(value)
        result[camel] = value
    return result


def load(data: Dict[str, Any], callback: Callable[..., Any], camelcase: bool) -> Any:
    data = data if not camelcase else to_snake(data)
    return callback(**data)
