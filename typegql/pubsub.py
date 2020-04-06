from typing import Optional

from graphql.pyutils import EventEmitter, EventEmitterAsyncIterator

__all__ = ("pubsub",)


class _PubSub:
    def __init__(self, loop=None):
        self._emitter: Optional[EventEmitter] = None
        self._loop = loop

    @property
    def emitter(self) -> EventEmitter:
        if not self._emitter:
            self._emitter = self._emitter = EventEmitter(self._loop)
        return self._emitter

    def subscribe(self, channel: str):
        return EventEmitterAsyncIterator(self.emitter, channel)

    def publish(self, channel: str, *args, **kwargs):
        self.emitter.emit(channel, *args, **kwargs)


pubsub = _PubSub()
