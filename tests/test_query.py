async def test__books_connection__ok(schema):
    query = """
    query BooksConnection {
      booksConnection {
        totalCount
        edges {
          node {
            id
            title
            published
          }
        }
      }
    }
    """
    result = await schema.run(query)
    assert result.data
    assert 'booksConnection' in result.data
    assert 'totalCount' in result.data['booksConnection']
    assert 'edges' in result.data['booksConnection']
    edges = result.data['booksConnection']['edges']
    assert edges and len(edges) > 0
    assert result


async def test__author_connection_with_enum__ok(schema):
    query = """
    query AuthorsConnection {
      authorsConnection {
        totalCount
        edges {
          node {
            id
            gender
          }
        }
      }
    }
    """
    result = await schema.run(query)
    assert result.data
    assert 'authorsConnection' in result.data
    assert 'totalCount' in result.data['authorsConnection']
    assert 'edges' in result.data['authorsConnection']
    edges = result.data['authorsConnection']['edges']
    assert edges and len(edges) > 0
    first_node = edges[0]['node']
    assert first_node['gender'] is not None
    assert result
