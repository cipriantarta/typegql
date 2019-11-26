from dataclasses import dataclass, field
from typing import List, Dict

from graphql import GraphQLResolveInfo

from typegql import ID, RequiredListInputArgument
from examples.library.types import Book, Author


@dataclass(init=False, repr=False)
class Mutation:
    create_books: List[ID] = field(metadata={
        'description': 'Create new `Book`s and return a list of ids for the created objects',
        'arguments': [
            RequiredListInputArgument[Book](name='books')
        ]})

    async def mutate_create_books(self, _: GraphQLResolveInfo, books: List[Dict]):
        return [1]

    create_authors: List[ID] = field(metadata={
        'description': 'Create new `Author`s and return a list of ids for the created objects',
        'arguments': [
            RequiredListInputArgument[Author](name='authors')
        ]})

    async def mutate_create_authors(self, _: GraphQLResolveInfo, authors: List[Dict]):
        return [1]
