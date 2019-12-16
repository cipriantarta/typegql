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


async def test__authors__ok(schema):
    query = """
        query Authors {
          authors {
            id
            name
            gender
            geo {
              latitude
              longitude
            }
          }
        }
        """
    result = await schema.run(query)
    assert result.data
    assert 'authors' in result.data
    assert len(result.data['authors']) > 0
    author = result.data['authors'][0]
    assert 'id' in author
    assert 'name' in author
    assert 'gender' in author
    assert 'geo' in author
    assert 'latitude' in author['geo']
    assert 'longitude' in author['geo']
