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
        books: List[Book] = Field()
        authors: List[Author] = Field()
        categories: List[Category] = Field()

        books_connection: Connection[Book] = Field(description='Relay connection')

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

    from dataclasses import dataclass
    from datetime import datetime
    from decimal import Decimal
    from enum import Enum
    from typing import List

    from typegql import Field, ID, OptionalField, ReadonlyField
    from typegql.core.graph import Graph
    from examples.library import db


    class Gender(Enum):
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


Using Fields instead
--------------------

You can use the following fields to define your GraphQL schema:

.. code-block:: python

    Field, InputField, RequiredField, OptionalField

For example:

.. code-block:: python

    from typegql import Field, Connection, OptionalField


    class Query(Graph):
        authors: Author = Field()
        categories: Category = Field(description="what's this?")
        books_connection: Connection[Book] = OptionalField()

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
2.0.9 [2019-10-29]
------------------
- changed the name of an input object from ObjectMuation to ObjectInput

2.0.8 [2019-10-15]
------------------
- allows forward reference between graph types (ie: `Book` has an `author` and an `Author` has `books`).
    this only works with python 3.7(using `from __future__ import annotations`, or python 3.8

2.0.6 [2019-06-24]
------------------
- updates uvloop dependency

2.0.5 [2019-04-24]
------------------
- fixed a bug when sending `introspection schema`

2.0.4 [2019-04-24]
------------------
- updates assert for introspection add message with status and result
- adds support for enum objects in `resolve_field_velue_or_error`

2.0.3 [2019-02-08]
------------------
- changes `Connection`, `Edge`, `Node` and `PageInfo` to interfaces `IConnection`, `IEdge`, etc.
- implements default `Connection` and `PageInfo` objects
- removes `has_next`, `has_previous` from `PageInfo`

2.0.1 [2019-01-19]
------------------
- all properties that don't have a `Field` instance assigned to them will be ignored by the `Schema`
- updates docs & example to reflect 2.0 changes
- fixed a bug when using a `List` argument in mutations

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
