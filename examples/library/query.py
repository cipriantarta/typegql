from typing import List, TypeVar, Generic

from graphql import GraphQLResolveInfo

from typegql import Graph, Connection, GraphInfo, GraphArgument, InputGraph, ID, Field, ArgumentList, ListField, \
    ConnectionField
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

    books_new_name: ListField[Book](name='books_new_name')
    books_connection: Field[CustomConnection[Book]](
        required=True,
        description='Showcasing Field[Type]',
        arguments=[
            ArgumentList[ID](name='for_authors', required=True, description='Filter books by author `ID`')])

    authors_connection: ConnectionField[Author](connection_class=CustomConnection)

    async def resolve_authors(self, selections):
        return [Author(**data) for data in db.get('authors')]

    async def resolve_books(self, info: GraphQLResolveInfo, author=None, **kwargs):
        if author:
            authors = [a['id'] for a in db.get('authors') if a['name'] == author]
            result = [Book(**book) for book in db.get('books') if book['author_id'] in authors]
        else:
            result = [Book(**book) for book in db.get('books')]
        return result

    async def resolve_books_new_name(self, info, author=None, **kwargs):
        return await self.resolve_books(info, author, **kwargs)

    async def resolve_categories(self, selections):
        return [Category(**data) for data in db.get('categories')]

    async def resolve_books_connection(self,
                                       info: GraphQLResolveInfo,
                                       for_authors: List[ID] = None,
                                       first: int = None,
                                       last: int = None,
                                       **kwargs):
        if for_authors:
            data = [Book(**book) for book in db.get('books') if book['author_id'] in [int(_id) for _id in for_authors]]
        else:
            data = [Book(**book) for book in db.get('books')]
        total = len(data)
        if first:
            data = data[:first]
        if last:
            data = data[-last:]

        return {
            'total_count': total,
            'page_info': {
                'has_next': False
            },
            'edges': [{
                'node': node
            } for node in data]}

    async def resolve_authors_connection(self, info, first=None, last=None, **kwargs):
        data = [Author(**author) for author in db.get('authors')]
        total = len(data)
        if first:
            data = data[:first]
        if last:
            data = data[-last:]
        return {
            'total_count': total,
            'page_info': {
                'has_next': False
            },
            'edges': [{
                'node': node
            } for node in data]}


class Mutation(InputGraph):
    create_books: List[ID]

    class Meta:
        create_books = GraphInfo(required=True,
                                 description='Create new `Book` objects and retrieve a list of ids for the '
                                             'created objects',
                                 arguments=[
                                     GraphArgument[List[Book]]('data', is_input=True)
                                 ])

    async def mutate_create_books(self, info: GraphQLResolveInfo, data):
        return [1]
