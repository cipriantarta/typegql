from dataclasses import dataclass, field
from typing import Dict, List

from graphql import GraphQLResolveInfo

from examples.library.types import Author, Book
from typegql import ID, RequiredListInputArgument
from typegql.pubsub import pubsub


@dataclass(init=False, repr=False)
class Mutation:
    create_books: List[ID] = field(
        metadata={
            "description": "Create new `Book`s and return a list of ids for the created objects",
            "arguments": [RequiredListInputArgument[Book](name="books")],
        }
    )

    async def mutate_create_books(self, _: GraphQLResolveInfo, books: List[Dict]):
        result = [1]
        pubsub.publish("books_added", result)
        return result

    create_authors: List[ID] = field(
        metadata={
            "description": "Create new `Author`s and return a list of ids for the created objects",
            "arguments": [RequiredListInputArgument[Author](name="authors")],
        }
    )

    async def mutate_create_authors(self, _: GraphQLResolveInfo, authors: List[Dict]):
        result = [1]
        pubsub.publish("authors_added", result)
        return result
