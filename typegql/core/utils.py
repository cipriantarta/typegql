from enum import Enum
from typing import Any, List

from .connection import Connection
from .graph import Graph


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
        return _type.__origin__ is Connection or issubclass(_type.__origin__, Connection)
    except (TypeError, AttributeError):
        return False
