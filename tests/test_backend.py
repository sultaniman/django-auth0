#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-auth0
------------
Tests for `django-auth0` auth_helpers module.
"""
from mock import patch
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


class MockObject(object):
    def json(self):
        return mock_user


def mock_request(*args, **kwargs):
    return MockObject()


def make_request():
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
    def test_login_process_returns_400(self, mock_get, mock_post):
        """ It returns HTTP 400 when profile data from Auth0 is empty """
        request = make_request()
        result = auth_helpers.process_login(request)
        self.assertEqual(result.status_code, 400)

    # @patch('django_auth0.auth_helpers.requests.get', side_effect=mock_request)
    # @patch('django_auth0.auth_helpers.requests.post', side_effect=mock_request)
    # def test_login_process_it_works(self, mock_get, mock_post):
    #     """ It returns HTTPRedirect when everything is ok """
    #     request = make_request()
    #     result = auth_helpers.process_login(request)
    #     print(result)
    #
    #     self.assertEqual(result.status_code, 420)
