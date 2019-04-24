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
