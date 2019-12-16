from dataclasses import dataclass
from typing import Sequence

from graphql.pyutils import EventEmitterAsyncIterator, EventEmitter

from typegql import ID


@dataclass(init=False, repr=False)
class Subscription:
    books_added: Sequence[ID]

    def __init__(self):
        self.emitter = EventEmitter()
        self.queue = EventEmitterAsyncIterator(self.emitter, 'library')

    async def on_books_added(self, data):
        return data
