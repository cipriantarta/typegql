from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Generic, List, Optional, TypeVar

from graphql import GraphQLResolveInfo

from examples.library import db
from examples.library.types import Author, Book, Category, Gender
from typegql import ID, Argument, ArgumentList, Connection

T = TypeVar("T")


@dataclass
class CustomConnection(Connection, Generic[T]):
    total_count: Optional[int] = field(default=None)

    @classmethod
    async def resolve(
        cls,
        source: Any,
        field_name: str,
        connection_type: T,
        info: GraphQLResolveInfo,
        **kwargs,
    ):
        func = getattr(source, f"resolve_{field_name}")
        return await func(info, **kwargs)


@dataclass(init=False, repr=False)
class Query:
    books: List[Book] = field(
        metadata={"arguments": [Argument[str](name="for_author_name")]}
    )
    authors: List[Author]
    categories: List[Category]

    books_new_name: List[Book] = field(metadata={"alias": "books_alias"})
    books_connection: CustomConnection[Book] = field(
        metadata={
            "description": "Relay connection",
            "arguments": [
                ArgumentList[ID](
                    name="for_authors", description="Filter books by author `ID`"
                )
            ],
        }
    )

    authors_connection: CustomConnection[Author]

    async def resolve_authors(self, _: GraphQLResolveInfo):
        authors = list()
        for author in db.get("authors"):
            data = deepcopy(author)
            data["gender"] = Gender(data["gender"])
            authors.append(Author.load(**data))

        for author in authors:
            author.books = [
                Book(**book)
                for book in db.get("books")
                if book["author_id"] == author.id
            ]

        return authors

    async def resolve_books(
        self, _: GraphQLResolveInfo, for_author_name: Optional[str] = None
    ):
        if for_author_name:
            authors = [
                a["id"] for a in db.get("authors") if a["name"] == for_author_name
            ]
            result = [
                Book(**book) for book in db.get("books") if book["author_id"] in authors
            ]
        else:
            result = [Book(**book) for book in db.get("books")]
        return result

    async def resolve_books_alias(self, info: GraphQLResolveInfo):
        return await self.resolve_books(info)

    async def resolve_categories(self, selections):
        return [Category(**data) for data in db.get("categories")]

    async def resolve_books_connection(
        self,
        _: GraphQLResolveInfo,
        for_authors: List[str] = None,
        first: int = None,
        last: int = None,
    ):
        if for_authors:
            data = [
                Book(**book)
                for book in db.get("books")
                if book["author_id"] in [int(_id) for _id in for_authors]
            ]
        else:
            data = [Book(**book) for book in db.get("books")]
        total = len(data)
        if first:
            data = data[:first]
        if last:
            data = data[-last:]

        return {
            "total_count": total,
            "page_info": {"has_next": False},
            "edges": [{"node": node} for node in data],
        }

    async def resolve_authors_connection(self, info, first=None, last=None, **kwargs):
        data = [Author.load(**author) for author in db.get("authors")]
        for a in data:
            if a.gender:
                a.gender = Gender(a.gender)  # Send gender as Enum not as string

        total = len(data)
        if first:
            data = data[:first]
        if last:
            data = data[-last:]
        return {
            "total_count": total,
            "page_info": {"has_next": False},
            "edges": [{"node": node} for node in data],
        }
