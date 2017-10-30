import pytest
from unittest.mock import Mock
from types import SimpleNamespace
from marshmallow import Schema, fields
from datetime import date as Date
from pyramid.testing import DummyRequest

from pyramid_apispec import view_validator, ValidationError


class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()


@pytest.fixture
def view():
    return Mock()


@pytest.fixture
def wrapped(view):
    info = SimpleNamespace(options={
        'validate': AlbumSchema(),
    })
    return view_validator(view, info)


def test_no_validate():
    view = Mock()
    info = SimpleNamespace(options={})
    assert view_validator(view, info) is view


def test_validate(wrapped, view):
    request = DummyRequest()
    request.method = 'POST'
    request.json_body = {
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }
    context = object()
    wrapped(context, request)
    view.assert_called_once_with(context, request)
    assert request.data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }


def test_validate_get(wrapped, view):
    request = DummyRequest()
    request.method = 'GET'
    request.GET = {
        'title': 'Hunky Dory',
        'release_date': '1971-12-17',
    }
    context = object()
    wrapped(context, request)
    view.assert_called_once_with(context, request)
    assert request.data == {
        'title': 'Hunky Dory',
        'release_date': Date(1971, 12, 17),
    }


def test_validate_error(wrapped, view):
    request = DummyRequest()
    request.method = 'POST'
    request.json_body = {
        'title': 'Hunky Dory',
        'release_date': '1971-14-17',
    }
    context = object()
    with pytest.raises(ValidationError) as exc:
        wrapped(context, request)
    assert exc.value.errors == {'release_date': ['Not a valid date.']}
