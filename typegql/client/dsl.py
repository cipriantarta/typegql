import collections
import decimal
from functools import partial

from graphql import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLString,
    OperationType,
    ast_from_value,
    print_ast,
)
from graphql.language import ast
from graphql.pyutils import FrozenList, snake_to_camel


class DSLField:
    def __init__(self, name, f, camelcase=True):
        self.field = f
        self.ast_field = ast.FieldNode(name=ast.NameNode(value=name), arguments=[])
        self.selection_set = None
        self.camelcase = camelcase

    def select(self, *fields):
        selection_nodes = list(selections(*fields))
        if not self.ast_field.selection_set:
            self.ast_field.selection_set = ast.SelectionSetNode(
                selections=FrozenList(selection_nodes)
            )
            return self

        selection_nodes.extend(self.ast_field.selection_set.selections)
        self.ast_field.selection_set = ast.SelectionSetNode(
            selections=FrozenList(selection_nodes)
        )
        return self

    def __call__(self, *args, **kwargs):
        return self.args(*args, **kwargs)

    def alias(self, alias):
        self.ast_field.alias = ast.NameNode(value=alias)
        return self

    def args(self, **kwargs):
        if self.camelcase:
            self.args_to_camelcase(kwargs)
        argument_nodes = list()
        for name, value in kwargs.items():
            arg = self.field.args.get(name)
            if not arg:
                raise ValueError(f"Invalid argument {name} for field {self.name}")
            arg_type_serializer = get_arg_serializer(arg.type)
            value = arg_type_serializer(value)

            argument_nodes.append(
                ast.ArgumentNode(
                    name=ast.NameNode(value=name), value=get_ast_value(value)
                )
            )
        self.ast_field.arguments = FrozenList(argument_nodes)
        return self

    def args_to_camelcase(self, arguments):
        if not isinstance(arguments, dict):
            return
        keys = [k for k in arguments.keys()]
        for key in keys:
            if isinstance(arguments[key], list):
                for arg in arguments[key]:
                    self.args_to_camelcase(arg)
            arguments[snake_to_camel(key, upper=False)] = arguments.pop(key)

    @property
    def ast(self):
        return self.ast_field

    @property
    def name(self):
        return self.ast.name.value


class DSLType(object):
    def __init__(self, _type, camelcase=True):
        self.type = _type
        self.camelcase = camelcase

    def __getattr__(self, name):
        formatted_name, field_def = self.get_field(name)
        return DSLField(formatted_name, field_def, camelcase=self.camelcase)

    def get_field(self, name):
        if self.camelcase:
            name = snake_to_camel(name, upper=False)
        if name in self.type.fields:
            return name, self.type.fields[name]
        raise KeyError("Field {} doesnt exist in type {}.".format(name, self.type.name))


class DSLSchema(object):
    def __init__(self, schema, camelcase=True):
        self.schema = schema
        self.camelcase = camelcase

    def __getattr__(self, name):
        type_def = self.schema.get_type(name)
        return DSLType(type_def, self.camelcase)

    def query(self, *fields, operation=OperationType.QUERY) -> ast.DocumentNode:
        return ast.DocumentNode(
            definitions=[
                ast.OperationDefinitionNode(
                    operation=operation,
                    selection_set=ast.SelectionSetNode(
                        selections=list(selections(*fields))
                    ),
                )
            ]
        )

    def mutation(self, *fields) -> ast.DocumentNode:
        return self.query(*fields, operation=OperationType.MUTATION)

    def as_string(self, doc):
        return print_ast(doc)


def field(f, **args):
    if isinstance(f, GraphQLField):
        return DSLField(f).args(**args)
    elif isinstance(f, DSLField):
        return f

    raise Exception('Received incompatible query field: "{}".'.format(field))


def selections(*fields):
    for _field in fields:
        yield field(_field).ast


def get_ast_value(value):
    if isinstance(value, ast.Node):
        return value
    if isinstance(value, ast.ValueNode):
        return value
    if isinstance(value, str):
        return ast.StringValueNode(value=value)
    elif isinstance(value, bool):
        return ast.BooleanValueNode(value=value)
    elif isinstance(value, (float, decimal.Decimal)):
        return ast.FloatValueNode(value=value)
    elif isinstance(value, int):
        return ast.IntValueNode(value=value)
    elif isinstance(value, list):
        return ast.ListValueNode(values=[get_ast_value(v) for v in value])
    return None


def serialize_list(serializer, values):
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, collections.Iterable):
        raise ValueError(f'Expected iterable, received "{repr(values)}"')
    result = list()
    for val in values:
        result.append(serializer(val))
    return result


def serialize_string(value):
    return ast.StringValueNode(value=value)


def serialize_enum(arg_type, value):
    return ast.EnumValueNode(value=arg_type.serialize(value))


def serialize_input_object(arg_type, value):
    serializers = {k: get_arg_serializer(v) for k, v in arg_type.fields.items()}
    result = ast_from_value(value, arg_type)
    for f in result.fields:
        serialized = serializers[f.name.value](value[f.name.value])
        if isinstance(f.value, ast.ListValueNode):
            f.value = ast.ListValueNode(values=serialized)
        else:
            f.value = serialized
    return result


def get_arg_serializer(arg_type):
    if isinstance(arg_type, GraphQLNonNull):
        return get_arg_serializer(arg_type.of_type)
    if arg_type == GraphQLString:
        return serialize_string
    if isinstance(arg_type, GraphQLInputField):
        return get_arg_serializer(arg_type.type)
    if isinstance(arg_type, GraphQLList):
        inner_serializer = get_arg_serializer(arg_type.of_type)
        return partial(serialize_list, inner_serializer)
    if isinstance(arg_type, GraphQLEnumType):
        return partial(serialize_enum, arg_type)
    if isinstance(arg_type, GraphQLInputObjectType):
        return partial(serialize_input_object, arg_type)
    return partial(serialize_value, arg_type)


def serialize_value(arg_type, value):
    return ast_from_value(
        str(value) if arg_type.serialize(value) is None else arg_type.serialize(value),
        arg_type,
    )
