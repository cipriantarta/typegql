from enum import Enum
from typing import Any, List, Callable, Dict, Union

from graphql.pyutils import camel_to_snake

from .connection import IConnection


def is_list(_type: Any) -> bool:
    try:
        return issubclass(_type.__origin__, List)
    except AttributeError:
        return False


def is_enum(_type: Any) -> bool:
    try:
        return issubclass(_type, Enum)
    except TypeError:
        return False


def is_connection(_type: Any) -> bool:
    try:
        return _type.__origin__ is IConnection or issubclass(_type.__origin__, IConnection)
    except (TypeError, AttributeError):
        return False


def is_optional(_type: Any) -> bool:
    if hasattr(_type, '__origin__') and _type.__origin__ == Union:
        if len(_type.__args__) == 2 and isinstance(None, _type.__args__[1]):
            return True
    return False


def to_snake(arguments: Dict, callback: Callable[[Dict], Any] = None) -> Dict[str, Any]:
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
    if callback:
        return callback(result)
    return result
