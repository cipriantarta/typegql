from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List

from typegql import Field, ID, OptionalField, ReadonlyField
from typegql.core.graph import Graph
from examples.library import db


class Gender(Enum):
    """Person\'s gender"""

    MALE = 'male'
    FEMALE = 'female'


class GeoLocation(Graph):
    latitude: Decimal = Field()
    longitude: Decimal = Field()

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


@dataclass
class Author(Graph):
    """Person that is usually a writer"""

    id: ID = ReadonlyField()
    name: str = Field()
    gender: Gender = OptionalField()
    geo: GeoLocation = OptionalField()
    books: List[Book] = OptionalField()


@dataclass
class Category(Graph):
    id: ID = ReadonlyField()
    name: str = Field()


@dataclass
class Book(Graph):
    """A book... for reading :|"""

    id: ID = ReadonlyField()
    author_id: ID = Field()
    title: str = OptionalField()
    author: Author = ReadonlyField(description='The author of this book')
    categories: List[Category] = OptionalField()
    published: datetime = OptionalField()
    tags: List[str] = OptionalField()

    def __post_init__(self):
        self.published = datetime.strptime(self.published, '%Y-%m-%d %H:%M:%S')

    async def resolve_author(self, info):
        data = filter(lambda x: x['id'] == self.author_id, db.get('authors'))
        data = next(data)
        author = Author(**data)
        author.gender = Gender[author.gender.upper()].value
        if 'geo' in data:
            author.geo = GeoLocation(**data.get('geo'))
        return author

    async def resolve_categories(self, selections, name=None):
        data = filter(lambda x: x['id'] in self.categories, db.get('categories'))
        for d in data:  # showcasing async generator
            yield Category(**d)

    def resolve_tags(self, selections):
        return ['testing', 'purpose']
