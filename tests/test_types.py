from datetime import datetime
from decimal import Decimal as DecimalType
from enum import Enum

import pytest
from graphql import FloatValueNode, StringValueNode, UndefinedType, ValueNode

from typegql.builder.types import DateTime, Decimal, Dictionary, EnumType


async def test__datetime_type__ok():
    dt = DateTime()

    # Parser
    with pytest.raises(UndefinedType):
        dt.parse_literal(StringValueNode(value="some weird date"))
    assert isinstance(dt.parse_literal(StringValueNode(value="2019-01-01")), datetime)
    assert dt.parse_literal(StringValueNode(value="2019-01-01")) == datetime(2019, 1, 1)
    with pytest.raises(UndefinedType):
        dt.parse_literal(ValueNode(value="2019-01-01"))

    # Serializer
    with pytest.raises(UndefinedType):
        dt.serialize("2019-01-01")
    assert dt.serialize(datetime(2019, 1, 1)) == "2019-01-01T00:00:00"


async def test__decimal_type__ok():
    dt = Decimal()

    # Parser
    with pytest.raises(UndefinedType):
        dt.parse_literal(FloatValueNode(value="pi"))
    assert isinstance(dt.parse_literal(FloatValueNode(value="3.14")), DecimalType)
    with pytest.raises(UndefinedType):
        dt.parse_literal(FloatValueNode(value="3,14"))

    # Serializer
    with pytest.raises(UndefinedType):
        dt.serialize("3.14")
    assert dt.serialize(3.14) == 3.14
    assert dt.serialize(3) == 3
    assert dt.serialize(DecimalType(3.14)) == 3.14


async def test__dictionary_type__ok():
    dt = Dictionary()
    # Parser
    assert dt.parse_literal(StringValueNode(value="{'foo': 1, 'bar': 2}")) == {
        "foo": 1,
        "bar": 2,
    }
    with pytest.raises(UndefinedType):
        dt.parse_literal(StringValueNode(value="{'foo': 1, 'bar': 2"))
    with pytest.raises(UndefinedType):
        dt.parse_literal(ValueNode(value="{'foo': 1}"))

    # Serializer
    assert dt.serialize({"foo": 1, "bar": 2}) == {"foo": 1, "bar": 2}
    with pytest.raises(UndefinedType):
        dt.serialize("{'foo': 1, 'bar': 2}")


class RGBEnum(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class CMYEnum(Enum):
    CYAN = "cyan"
    MAGENTA = "magenta"
    YELLOW = "yellow"


async def test__enum_type__ok():
    et = EnumType("TestEnum", RGBEnum)
    assert et.serialize(RGBEnum.RED) == RGBEnum.RED.name
    with pytest.raises(UndefinedType):
        et.serialize("RED")
    assert et.values["RED"].value == RGBEnum.RED

    with pytest.raises(UndefinedType):
        et.serialize(CMYEnum.CYAN)
