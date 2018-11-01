.. role:: python(code)
    :language: python

AIOGraph
========

A Python `GraphQL <https://graphql.org>`_ library that makes use of type hinting and concurrency support with the new async/await syntax.


DISCLAIMER
==========

This library is still in it's infancy, so **use with caution** and feel free to contribute.


Installation
============

.. code-block:: python

    pip install git+https://github.com/cipriantarta/aiograph


Usage
=====

The following demonstrates how to use **aiograph** for implementing a *GraphQL API* for a library of books.
The example can be found in *aiograph/core/examples* and you can run it with Sanic by executing ``python <path_to_example>/server.py``

Define your query
-----------------

.. code-block:: python

    from aiograph.core.types import Graph, Connection
    from aiograph.examples.library.types import Author, Category
    from aiograph.examples.library.types import Book
    from aiograph.examples.library import db

    class Query(Graph):
        books: Connection[Book]
        authors: Connection[Author]
        categories: Connection[Category]

        async def resolve_authors(self, selections):
            return db.get('authors')

        async def resolve_books(self, selections, name=None):
            return db.get('books')

        async def resolve_categories(self, selections):
            return db.get('categories')


Define your types
-----------------

.. code-block:: python

    from enum import Enum
    from typing import List

    from aiograph.core.types import Graph, Connection
    from aiograph.examples.library import db


    class Book(Graph):
        id: int
        author_id: int
        title: str
        author: Connection['Author']
        categories: Connection[List['Category']]

        async def resolve_author(self, selections, name=None):
            data = filter(lambda x: x['id'] == self.author_id, db.get('authors'))
            return next(data)

        async def resolve_categories(self, selections, name=None):
            data = filter(lambda x: x['id'] in self.categories, db.get('categories'))
            return list(data)


    class Gender(Enum):
        MALE = 'male'
        FEMALE = 'female'


    class Author(Graph):
        id: int
        name: str
        books: Connection[Book]
        gender: Gender


    class Category(Graph):
        id: str
        name: str
        books: Connection[Book]


Run your query
--------------

.. code-block:: python

    from aiograph.core.schema import Schema
    from aiograph.examples.library.query import Query

    async def run():
        schema = Schema(Query)
        result = await schema.run(graph)


Change Log
==========

    - added `graphql-core-next <https://github.com/graphql-python/graphql-core-next>`_ as a baseline for all GraphQL operations
