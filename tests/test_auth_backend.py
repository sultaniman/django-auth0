#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django-auth0` models module.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django_auth0.auth_backend import Auth0Backend


class TestDjangoAuth0(TestCase):
    """ Test Auth0Backend """

    def setUp(self):
        self.backend = Auth0Backend()
        self.auth_data = {
            'email': 'email@email.com',
            'nickname': 'test_username'
        }

    def test_authenticate_works(self):
        """ Authenticate works ok """
        user = self.backend.authenticate(**self.auth_data)
        self.assertTrue(isinstance(user, User), msg='user is instance of User')

    def test_authenticate_creates_user(self):
        """ Authenticate works creates a user """
        user = self.backend.authenticate(**self.auth_data)
        self.assertIsNotNone(user, msg='User exists')

    def test_authenticate_fires_exception(self):
        """ Authenticate fires exception when insufficient data supplied """
        self.assertRaises(ValueError, self._value_error)
        self.assertRaises(KeyError, self.backend.authenticate)

    def _value_error(self):
        self.auth_data['email'] = None
        return self.backend.authenticate(**self.auth_data)
