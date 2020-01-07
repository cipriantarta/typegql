from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from typegql import ID
from examples.library import db


class Gender(Enum):
    """Person\'s gender"""

    MALE = 'male'
    FEMALE = 'female'


@dataclass
class GeoLocation:
    latitude: Decimal
    longitude: Decimal


@dataclass
class Author:
    """Person that is usually a writer"""

    id: ID = field(metadata={'readonly': True})
    name: str
    password: str = field(metadata={'skip': True})  # Ignore this field when building the schema
    gender: Optional[Gender] = None
    geo: Optional[GeoLocation] = None
    books: Optional[List[Book]] = None

    @classmethod
    def load(cls, **data):  # can be used to manipulate / validate input data
        data = {'id': None, 'password': '', **data}
        return cls(**data)


@dataclass
class Category:
    id: ID = field(metadata={'readonly': True})
    name: str


@dataclass
class Book:
    """A book... for reading :|"""

    id: ID = field(metadata={'readonly': True})
    author_id: ID
    title: str
    author: Optional[Author] = field(default=None, metadata={'description': 'The author of this book'})
    categories: Optional[List[Category]] = None
    published: Optional[datetime] = None
    tags: Optional[List[str]] = None

    def __post_init__(self):
        self.published = datetime.strptime(self.published, '%Y-%m-%d %H:%M:%S')

    async def resolve_author(self, info):
        data = filter(lambda x: x['id'] == self.author_id, db.get('authors'))
        data = next(data)
        author = Author.load(**data)
        author.gender = Gender(author.gender)
        if 'geo' in data:
            author.geo = GeoLocation(**data.get('geo'))
        return author

    async def resolve_categories(self, selections, name=None):
        data = filter(lambda x: x['id'] in self.categories, db.get('categories'))
        for d in data:  # showcasing async generator
            yield Category(**d)

    def resolve_tags(self, selections):
        return ['testing', 'purpose']
