from typing import get_type_hints


class Graph:
    def __init__(self, **kwargs):
        for name, _ in get_type_hints(self.__class__).items():
            if name not in kwargs:
                continue
            setattr(self, name, kwargs.get(name))


InputGraph = Graph
