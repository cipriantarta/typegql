async def test__books_connection__ok(schema):
    query = '''
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
    '''
    result = await schema.run(query)
    assert result.data
    assert 'booksConnection' in result.data
    assert 'totalCount' in result.data['booksConnection']
    assert 'edges' in result.data['booksConnection']
    edges = result.data['booksConnection']['edges']
    assert edges and len(edges) > 0
    assert result
