from typing import List, TypeVar, Generic

from graphql import GraphQLResolveInfo

from aiograph.core.graph import Graph, Connection, GraphInfo, GraphArgument
from aiograph.core.types import ID
from examples.library.types import Author, Category
from examples.library.types import Book
from examples.library import db

T = TypeVar('T', bound=Graph)


class CustomConnection(Connection, Generic[T]):
    total_count: int


class Query(Graph):
    books: List[Book]
    authors: List[Author]
    categories: List[Category]

    books_connection: CustomConnection[Book]

    class Meta:
        authors = ('Author', 'Collection of book authors')
        books_connection = GraphInfo(description='GraphQL connection that returns a collection of `Book`s',
                                     arguments=[
                                         GraphArgument[List[ID]](name='for_authors',
                                                                 description='Filter books by author `ID`')
                                     ])

    async def resolve_authors(self, selections):
        return [Author(**data) for data in db.get('authors')]

    async def resolve_books(self, info: GraphQLResolveInfo, author=None, **kwargs):
        if author:
            authors = [a['id'] for a in db.get('authors') if a['name'] == author]
            result = [Book(**book) for book in db.get('books') if book['author_id'] in authors]
        else:
            result = [Book(**book) for book in db.get('books')]
        return result

    async def resolve_categories(self, selections):
        return [Category(**data) for data in db.get('categories')]

    async def resolve_books_connection(self, info, for_authors: List[ID]=None):
        if for_authors:
            data = [Book(**book) for book in db.get('books') if book['author_id'] in [int(_id) for _id in for_authors]]
        else:
            data = [Book(**book) for book in db.get('books')]
        total = len(data)
        return {
            'total_count': total,
            'edges': [{
                'node': node
            } for node in data]}
