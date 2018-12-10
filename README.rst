.. role:: python(code)
    :language: python

TypeGQL
========

A Python `GraphQL <https://graphql.org>`_ library that makes use of type hinting and concurrency support with the new async/await syntax.


DISCLAIMER
==========

This library is still in it's infancy, so **use with caution** and feel free to contribute.


Installation
============

.. code-block:: python

    pip install typegql


Usage
=====

The following demonstrates how to use **typegql** for implementing a *GraphQL API* for a library of books.
The example can be found in *typegql/core/examples* and you can run it with Sanic by executing ``python <path_to_example>/server.py``

Define your query
-----------------

.. code-block:: python

    from typing import List
    from typegql.core.graph import Graph, Connection
    from typegql.examples.library.types import Author, Category
    from typegql.examples.library.types import Book
    from typegql.examples.library import db

    class Query(Graph):
        books: List[Book]
        authors: List[Author]
        categories: List[Category]

        books_connection: Connection[Book]

        async def resolve_authors(self, info, **kwargs):
            return db.get('authors')

        async def resolve_books(self, info, **kwargs):
            return db.get('books')

        async def resolve_categories(self, info, **kwargs):
            return db.get('categories')

       async def resolve_books_connection(self, info, **kwargs):
            data = db.get('books')
            return {
                'edges': [{
                    'node': node
                } for node in data]}


Define your types
-----------------

.. code-block:: python

    from datetime import datetime
    from decimal import Decimal
    from enum import Enum
    from typing import List

    from typegql.core.graph import Graph, ID, GraphInfo
    from examples.library import db


    class Gender(Enum):
        MALE = 'male'
        FEMALE = 'female'


    class GeoLocation:
        latitude: Decimal
        longitude: Decimal

        def __init__(self, latitude, longitude):
            self.latitude = latitude
            self.longitude = longitude


    class Author(Graph):
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
        title: str
        author: Author
        categories: List[Category]
        published: datetime
        tags: List[str]

        class Meta:
            description = 'Just a book'
            id = GraphInfo(required=True, description='Book unique identifier')

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


Using Fields instead
--------------------

Instead of relying on Meta to define properties you can use the following fields:

.. code-block:: python

    Field, InputField, ConnectionField

For example:

.. code-block:: python

    from typegql import Field, ConnectionField


    class Query(Graph):
        authors: Field[Author]
        categories: Field[Category](description='what\'s this?', required=True)
        books_connection: ConnectionField[Book](connection_class=CustomConnection)

You can also pass arguments either in the Meta or as a Field argument

.. code-block:: python

    from typegql import Argument, ArgumentList, Field


    class Query(Graph):
        authors: Field[Author](arguments=[
            Argument[ID](name='id', required=True, mutation=True)
        ])
        books: List[Book]

        class Meta:
            books = GraphInfo(mutation=False, arguments=[
                ArgumentList[ID](name='authors')
            ])

Run your query
--------------

.. code-block:: python

    from typegql.core.schema import Schema
    from examples.library.query import Query


    schema = Schema(Query)
    query = '''
    query BooksConnection {
      books_connection {
        edges {
          node {
            id
            title
            published
            author {
              id
              name
            }
          }
        }
      }
    }
    '''

    async def run():
        result = await schema.run(query)

Client
======

TypeGQL supports DSL client for working with a GraphQL API.
The client automatically converts snake to camelcase. set `camelcase=False` if this is not desired

.. code-block:: python

    pip install typegql[client]

For example:


.. code-block:: python

    from typegql.client import Client

    async with Client(url, camelcase=True) as client:
        await client.introspection()
        dsl = client.dsl
        query = dsl.Query.books_connection.select(dsl.BooksConnection.total_count)
        doc = dsl.query(query)

        status, result = await client.execute(doc)

Change Log
==========
1.0.7 [2018-12-09]
------------------
- bug fixing
- adds support for camelcase in Client

1.0.1 [2018-11-19]
------------------
- adds support for client DSL

Initial
-------
- added `graphql-core-next <https://github.com/graphql-python/graphql-core-next>`_ as a baseline for all GraphQL operations


TODO
====
- testing
- travis
- more testing
- please help with testing :|
