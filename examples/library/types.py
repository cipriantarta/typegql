from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List

from typegql import Field
from typegql.core.graph import Graph, ID, GraphInfo
from examples.library import db


class Gender(Enum):
    """Person\'s gender"""

    MALE = 'male'
    FEMALE = 'female'


class GeoLocation:
    latitude: Decimal
    longitude: Decimal

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


class Author(Graph):
    """Person that is usually a writer"""

    id: ID
    name: str
    gender: Gender
    geo: GeoLocation


class Category(Graph):
    id: ID
    name: str


class Book(Graph):
    id: ID
    author_id: ID
    title: Field[str]
    author: Field[Author](required=True, description='The author of this book')
    categories: List[Category]
    published: datetime
    tags: List[str]

    class Meta:
        description = 'Just a book'
        id = GraphInfo(required=True, use_in_mutation=False, description='Book unique identifier')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
