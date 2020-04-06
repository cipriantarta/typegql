.. role:: python(code)
    :language: python

TypeGQL
========

A Python `GraphQL <https://graphql.org>`_ library that makes use of type hinting and concurrency support with the new async/await syntax.
With the help of type hints and dataclass it's easy to build a GraphQL schema using nothing but Python objects and primitives

**Consider the following:**

.. code-block:: python

    from graphql import (
        GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString)

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='RootQueryType',
            fields={
                'hello': GraphQLField(
                    GraphQLString,
                    resolve=lambda obj, info: 'world')
            }))

**Versus:**

.. code-block:: python

    from dataclasses import dataclass
    from typegql import Schema

    @dataclass(init=False)
    class RootQuery:
        hello: str

    def resolve_hello(info):
        return 'world

     schema = Schema(query=RootQuery)

Clearly the second one looks more "Pythonic" and it's easier to maintain for complex structures

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

    from dataclasses import dataclass
    from typing import List
    from typegql import Connection
    from typegql.examples.library.types import Author, Category
    from typegql.examples.library.types import Book
    from typegql.examples.library import db


    @dataclass(init=False, repr=False)
    class Query:
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

    from dataclasses import dataclass, field
    from datetime import datetime
    from decimal import Decimal
    from enum import Enum
    from typing import List

    from examples.library import db


    class Gender(Enum):
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
        gender: Optional[Gender] = None
        geo: Optional[GeoLocation] = None
        books: Optional[List[Book]] = None


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
            author = Author(**data)
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


Run your query
--------------

.. code-block:: python

    from typegql import Schema
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
The client automatically converts snake to camelcase. Set `camelcase=False` if this is not desired.

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
4.0.2 [2020-04-06]
------------------
- updates graphql-core to 3.1.0

4.0.1 [2020-03-17]
------------------
- fixes enum return value

4.0.0 [2020-03-16]
------------------
- BREAKING CHANGES:
    - `Schema` now accepts a more granular list of custom graphql types. Signature is:

.. code-block:: python

        def __init__(self,
                 query: Type,
                 mutation: Optional[Type] = None,
                 subscription: Optional[Type] = None,
                 scalars: Optional[GraphQLScalarMap] = None,
                 enums: Optional[GraphQLEnumMap] = None,
                 interfaces: Optional[GraphQLInterfaceMap] = None,
                 query_types: Optional[GraphQLObjectTypeMap] = None,
                 mutation_types: Optional[GraphQLInputObjectTypeMap] = None,
                 camelcase=True):

3.1.0 [2020-01-29]
------------------
- fixes an issue with camelcase parameters when a `load` method is provided

3.0.9 [2020-01-13]
------------------
- fix client execution function
- update `dsl` selections to work with `FrozenList`

3.0.8 [2020-01-07]
------------------
- added ability to ignore attributes in building the schema by using `field(metadata={'skip': True})`. This can be useful when you don't want to expose certain fields in GraphQL, like a user's `password` for example.

3.0.5 [2019-12-16]
------------------
- added support for subscriptions

3.0.4 [2019-12-04]
------------------
- updates `graphql-core-next` to `grapqhl-core` >= 3
- use Sequence instead of List where possible

3.0.3 [2019-11-29]
------------------
- fixed a bug where a custom connection arguments don't include the relay pagination arguments as well

3.0.2 [2019-11-26]
------------------
- PEP 561 compliant

3.0.1 [2019-11-26]
------------------
- BREAKING: Removed `Graph` as a baseclass
- now makes use of `dataclasses.dataclass` and `dataclasess.fields` for building the `Schema`
- bug fixing and improvements

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
