from typing import Dict, Union

from graphql import GraphQLField, GraphQLInputField


class GraphHelper:
    def __init__(self, graph, builder, is_mutation):
        self.graph = graph
        self.builder = builder
        self.is_mutation = is_mutation

    def get_fields(self) -> Dict[str, Union[GraphQLField, GraphQLInputField]]:
        return self.builder.get_fields(self.graph, is_mutation=self.is_mutation)
