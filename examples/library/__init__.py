# flake8: noqa

import json

db = json.loads('''
{
  "authors": [
    {"id": 1, "name": "J.R.R. Tolkien", "gender": "male", "geo": {"latitude": 40.697403, "longitude": -74.120107}},
    {"id": 2, "name": "Christopher Hitchens", "gender": "male"}
  ],
  "books": [
    {"id": 1, "author_id": 1, "title": "Lord of the Rings", "categories": [1, 3], "published": "2017-03-10 13:30:00"},
    {"id": 2, "author_id": 1, "title": "The Hobbit", "categories": [1, 3], "published": "2017-03-10 13:30:00"},
    {"id": 3, "author_id": 2, "title": "Mortality", "categories": [2], "published": "2017-03-10 13:30:00"}
  ],
  "categories": [
    {"id": 1, "name": "Fiction & Literature"},
    {"id": 2, "name": "Biography"},
    {"id": 3, "name": "Epic"}
  ]
}
''')
