from datetime import datetime
from decimal import Decimal as DecimalType
from enum import Enum

from graphql import StringValueNode, FloatValueNode, ValueNode
from graphql.error import InvalidType

from typegql.builder.types import DateTime, Decimal, Dictionary, EnumType


async def test__datetime_type__ok():
    dt = DateTime()

    # Parser
    assert isinstance(dt.parse_literal(StringValueNode(value='some weird date')), InvalidType)
    assert isinstance(dt.parse_literal(StringValueNode(value='2019-01-01')), datetime)
    assert dt.parse_literal(StringValueNode(value='2019-01-01')) == datetime(2019, 1, 1)
    assert isinstance(dt.parse_literal(ValueNode(value='2019-01-01')), InvalidType)

    # Serializer
    assert isinstance(dt.serialize('2019-01-01'), InvalidType)
    assert dt.serialize(datetime(2019, 1, 1)) == '2019-01-01T00:00:00'


async def test__decimal_type__ok():
    dt = Decimal()

    # Parser
    assert isinstance(dt.parse_literal(FloatValueNode(value='pi')), InvalidType)
    assert isinstance(dt.parse_literal(FloatValueNode(value='3.14')), DecimalType)
    assert isinstance(dt.parse_literal(FloatValueNode(value='3,14')), InvalidType)

    # Serializer
    assert isinstance(dt.serialize('3.14'), InvalidType)
    assert dt.serialize(3.14) == 3.14
    assert dt.serialize(3) == 3
    assert dt.serialize(DecimalType(3.14)) == 3.14


async def test__dictionary_type__ok():
    dt = Dictionary()
    # Parser
    assert dt.parse_literal(StringValueNode(value="{'foo': 1, 'bar': 2}")) == {'foo': 1, 'bar': 2}
    assert isinstance(dt.parse_literal(StringValueNode(value="{'foo': 1, 'bar': 2")), InvalidType)
    assert isinstance(dt.parse_literal(ValueNode(value="{'foo': 1}")), InvalidType)

    # Serializer
    assert dt.serialize({'foo': 1, 'bar': 2}) == {'foo': 1, 'bar': 2}
    assert isinstance(dt.serialize("{'foo': 1, 'bar': 2}"), InvalidType)


class RGBEnum(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'


class CMYEnum(Enum):
    CYAN = 'cyan'
    MAGENTA = 'magenta'
    YELLOW = 'yellow'


async def test__enum_type__ok():
    et = EnumType('TestEnum', RGBEnum)
    assert et.serialize(RGBEnum.RED) == RGBEnum.RED.value
    assert isinstance(et.serialize('RED'), InvalidType)
    assert et.values['RED'].value == RGBEnum.RED

    assert isinstance(et.serialize(CMYEnum.CYAN), InvalidType)
