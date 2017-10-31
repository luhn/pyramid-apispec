import pytest
from unittest.mock import Mock
from types import SimpleNamespace
from datetime import date as Date
from marshmallow import Schema, fields

from pyramid_apispec import view_marshaller, MarshalError


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


@pytest.fixture
def wrap_view():
    def wrap(view):
        info = SimpleNamespace(options={
            'marshal': AlbumSchema(),
        })
        return view_marshaller(view, info)

    return wrap


def test_marshal(wrap_view):
    unwrapped = Mock(return_value={
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    })
    view = wrap_view(unwrapped)
    assert view('context', 'request') == {
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }
    unwrapped.assert_called_once_with('context', 'request')


def test_marshal_error(wrap_view):
    unwrapped = Mock(return_value={
        'title': 'Hunky Dory',
        'release_date': 'whatever',
    })
    view = wrap_view(unwrapped)
    with pytest.raises(MarshalError) as exc:
        view('context', 'request')
    assert exc.value.errors == {
        'release_date': ['"whatever" cannot be formatted as a date.'],
    }
    unwrapped.assert_called_once_with('context', 'request')
