import collections
import decimal
from functools import partial

from graphql import GraphQLField, print_ast, ast_from_value, GraphQLNonNull, GraphQLInputField, GraphQLList, \
    GraphQLEnumType, GraphQLInputObjectType, OperationType, GraphQLString
from graphql.language import ast
from graphql.pyutils import snake_to_camel


class DSLField:
    def __init__(self, name, f):
        self.field = f
        self.ast_field = ast.FieldNode(name=ast.NameNode(value=name), arguments=[])
        self.selection_set = None

    def select(self, *fields):
        if not self.ast_field.selection_set:
            self.ast_field.selection_set = ast.SelectionSetNode(selections=[])
        self.ast_field.selection_set.selections.extend(selections(*fields))
        return self

    def __call__(self, *args, **kwargs):
        return self.args(*args, **kwargs)

    def alias(self, alias):
        self.ast_field.alias = ast.NameNode(value=alias)
        return self

    def args(self, **args):
        for name, value in args.items():
            arg = self.field.args.get(name)
            if not arg:
                name = snake_to_camel(name, upper=False)
                arg = self.field.args.get(name)
            assert arg, f'Invalid argument {name} for field {self.name}'
            arg_type_serializer = get_arg_serializer(arg.type)
            value = arg_type_serializer(value)
            self.ast_field.arguments.append(
                ast.ArgumentNode(
                    name=ast.NameNode(value=name),
                    value=get_ast_value(value)
                )
            )
        return self

    @property
    def ast(self):
        return self.ast_field

    @property
    def name(self):
        return self.ast.name.value


class DSLType(object):
    def __init__(self, type):
        self.type = type

    def __getattr__(self, name):
        formatted_name, field_def = self.get_field(name)
        return DSLField(formatted_name, field_def)

    def get_field(self, name):
        camel_cased_name = snake_to_camel(name, upper=False)

        if name in self.type.fields:
            return name, self.type.fields[name]

        if camel_cased_name in self.type.fields:
            return camel_cased_name, self.type.fields[camel_cased_name]

        raise KeyError('Field {} doesnt exist in type {}.'.format(name, self.type.name))


class DSLSchema(object):
    def __init__(self, schema):
        self.schema = schema

    def __getattr__(self, name):
        type_def = self.schema.get_type(name)
        return DSLType(type_def)

    def query(self, *fields, operation=OperationType.QUERY) -> ast.DocumentNode:
        return ast.DocumentNode(
            definitions=[ast.OperationDefinitionNode(
                operation=operation,
                selection_set=ast.SelectionSetNode(
                    selections=list(selections(*fields))
                )
            )]
        )

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
    assert isinstance(values, collections.Iterable), 'Expected iterable, received "{}"'.format(repr(values))
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
    result = ast_from_value(value)
    for field in result.fields:
        serialized = serializers[field.name.value](value[field.name.value])
        if isinstance(field.value, ast.ListValueNode):
            field.value = ast.ListValueNode(values=serialized)
        else:
            field.value = serialized
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
    return lambda value: ast_from_value(str(value) if arg_type.serialize(value) is None else arg_type.serialize(value))
