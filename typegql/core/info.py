import dataclasses
from typing import List

from .arguments import GraphArgument


@dataclasses.dataclass
class GraphInfo:
    name: str = dataclasses.field(default='')
    required: bool = dataclasses.field(default=False)
    use_in_mutation: bool = dataclasses.field(default=True)
    description: str = dataclasses.field(default='')
    arguments: List[GraphArgument] = dataclasses.field(default_factory=list)
