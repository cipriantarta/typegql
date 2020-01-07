from dataclasses import dataclass, field

from typegql import Schema


async def test__introspection__ok(schema, introspection_query):
    result = await schema.run(introspection_query)
    assert result.data
    assert '__schema' in result.data
    text = str(result.data)
    assert 'books' in text
    assert 'authors' in text
    assert 'categories' in text
    assert 'booksAlias' in text
    assert 'booksConnection' in text
    assert 'authorsConnection' in text


async def test__skip_attr__ok(introspection_query):
    @dataclass(init=False)
    class Query:
        foo: str
        bar: str = field(metadata={'skip': True})

    schema = Schema(Query)
    result = await schema.run(introspection_query)

    for _type in result.data['__schema']['types']:
        if _type['name'] == Query.__name__:
            assert len(_type['fields']) == 1
            assert _type['fields'][0]['name'] != 'bar'
            break
    assert True
