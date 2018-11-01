async def test__books_connection__ok(schema):
    query = '''
    query BooksConnection {
      books_connection {
        total_count
        edges {
          node {
            id
            title
            published
          }
        }
      }
    }
    '''
    result = await schema.run(query)
    assert result.data
    assert 'books_connection' in result.data
    assert 'total_count' in result.data['books_connection']
    assert 'edges' in result.data['books_connection']
    edges = result.data['books_connection']['edges']
    assert edges and len(edges) > 0
    assert result
