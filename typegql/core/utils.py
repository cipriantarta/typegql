from enum import Enum
from typing import Any, List

from .graph import Graph
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


def is_graph(_type: Any) -> bool:
    try:
        return issubclass(_type, Graph)
    except TypeError:
        return False


def is_connection(_type: Any) -> bool:
    try:
        return _type.__origin__ is IConnection or issubclass(_type.__origin__, IConnection)
    except (TypeError, AttributeError):
        return False
