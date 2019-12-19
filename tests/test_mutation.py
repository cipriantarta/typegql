from graphql import ExecutionResult


async def test__create_books__ok(schema):
    mutation = """
    mutation BooksMutation {
      createBooks(books: [{authorId: "MQ==", title: "New book"}])
    }
    """

    result = await schema.run(mutation)
    assert isinstance(result, ExecutionResult)
    assert result.errors is None
    assert 'createBooks' in result.data
    assert isinstance(result.data['createBooks'], list)
    assert len(result.data['createBooks']) > 0


async def test__create_books_with_invalid_date__raise_invalid_type(schema):
    mutation = """
    mutation BooksMutation {
      createBooks(books: [{authorId: "MQ==", title: "New book", published: "2019-02-45"}])
    }
    """
    result = await schema.run(mutation)
    assert isinstance(result, ExecutionResult)
    assert result.errors
    assert 'Expected type DateTime' in result.errors[0].message


async def test__create_books_with_valid_date__ok(schema):
    mutation = """
    mutation BooksMutation {
      createBooks(books: [{authorId: "MQ==", title: "New book", published: "2019-02-15 13:30:00"}])
    }
    """
    result = await schema.run(mutation)
    assert isinstance(result, ExecutionResult)
    assert result.errors is None


async def test__create_authors_with_invalid_decimal__raise_invalid_type(schema):
    mutation = """
    mutation AuthorsMutation {
      createAuthors(authors: [
        {name: "George R. R. Martin", gender: MALE, geo: {latitude: "some", longitude: "string"}}
      ])
    }
    """
    result = await schema.run(mutation)
    assert isinstance(result, ExecutionResult)
    assert result.errors
    assert 'Expected type Decimal' in result.errors[0].message


async def test__create_authors_with_valid_decimal__ok(schema):
    mutation = """
    mutation AuthorsMutation {
      createAuthors(authors: [
        {name: "George R. R. Martin", gender: MALE, geo: {latitude: 40, longitude: "-74.175524"}}
      ])
    }
    """
    result = await schema.run(mutation)
    assert isinstance(result, ExecutionResult)
    assert result.errors is None
