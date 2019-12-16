from graphql import ExecutionResult


async def test__create_books__ok(schema):
    mutation = """
    mutation BooksMutation {
      createBooks(books: [{authorId: "MQ==", title: "New bookx"}])
    }
    """

    result = await schema.run(mutation)
    assert isinstance(result, ExecutionResult)
    assert result.errors is None
    assert 'createBooks' in result.data
    assert isinstance(result.data['createBooks'], list)
    assert len(result.data['createBooks']) > 0
