from marshmallow import Schema
from pyramid.viewderivers import VIEW

from .spec import create_spec
from .exceptions import SchemaError, ValidationError, MarshalError


__all__ = [
    'SchemaError',
    'ValidationError',
    'MarshalError',
]


def includeme(config):
    # Stop introspecting, temporarily
    introspection = getattr(config, 'introspection', True)
    config.introspection = False

    config.add_view_deriver(view_validator)
    config.add_view_deriver(view_marshaller, under='rendered_view', over=VIEW)
    config.add_route('swagger', '/swagger')
    config.add_view(swagger, route_name='swagger', renderer='json')

    config.introspection = introspection


def _make_schema(schema):
    """
    If passed a schema, nothing happens.  If passed a dictionary, create a
    schema for one-time use.

    """
    if schema is None:
        return None
    elif isinstance(schema, Schema):
        return schema
    elif isinstance(schema, dict):
        _Schema = type('_Schema', (Schema,), schema.copy())
        return _Schema()
    else:
        raise TypeError('Schema is of invalid type.')


def view_validator(view, info):
    schema = _make_schema(info.options.get('validate'))
    if schema is None:
        return view

    def wrapped(context, request):
        if request.method == 'GET':
            data = dict(request.GET)
        else:
            data = request.json_body
        result = schema.load(data)
        if result.errors:
            raise ValidationError(result.errors)
        request.data = result.data
        return view(context, request)

    return wrapped


view_validator.options = ('validate',)


def view_marshaller(view, info):
    schema = _make_schema(info.options.get('marshal'))
    if schema is None:
        return view

    def wrapped(context, request):
        output = view(context, request)
        result = schema.dump(output)
        if result.errors:
            raise MarshalError(result.errors)
        return result.data

    return wrapped


view_marshaller.options = ('marshal',)


def swagger(context, request):
    introspector = request.registry.introspector
    spec = create_spec(introspector)
    return spec.to_dict()
