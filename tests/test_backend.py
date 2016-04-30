#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django-auth0` auth_helpers module.
"""
from mock import patch
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware

from django_auth0 import auth_helpers


mock_user = {
    'username': 'username',
    'email': 'email@email.com',
    'access_token': 'access_token'
}

user = User.objects.create_user(username=mock_user['username'], email=mock_user['email'])


class MockObject(object):
    def json(self):
        return mock_user


def mock_auth(*args, **kwargs):
    """ Returns creates test user and assigns authentication backend """
    setattr(user, 'backend', 'django_auth0.auth_backends.Auth0Backend')
    return user


def mock_request(*args, **kwargs):
    """ Returns mocked object call result for requests.join """
    return MockObject()


def make_request():
    """ Creates request factory object with session and url params """
    factory = RequestFactory()
    url = reverse('auth_callback')
    request = factory.get('%s/?code=code' % url)
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()

    return request


class TestDjangoAuth0(TestCase):
    @patch('django_auth0.auth_helpers.requests.get', side_effect=mock_request)
    @patch('django_auth0.auth_helpers.requests.post', side_effect=mock_request)
    def test_login_process_returns_400(self, *args, **kwargs):
        """ It returns HTTP 400 when profile data from Auth0 is empty """
        request = make_request()
        result = auth_helpers.process_login(request)
        self.assertEqual(result.status_code, 400, msg='Bad request returned')

    @patch('django_auth0.auth_helpers.requests.get', side_effect=mock_request)
    @patch('django_auth0.auth_helpers.requests.post', side_effect=mock_request)
    @patch('django_auth0.auth_helpers.authenticate', side_effect=mock_auth)
    def test_login_process_it_works(self, *args, **kwargs):
        """ It returns HTTPRedirect when everything is ok """
        request = make_request()
        result = auth_helpers.process_login(request)

        self.assertEqual(result.status_code, 302, msg='Success redirect happens')
        self.assertIsInstance(result, HttpResponseRedirect, msg='Correct redirect class used')
