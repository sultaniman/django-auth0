#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django-auth0` authentication backend.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django_auth0.auth_backend import Auth0Backend


def _get_user(backend):
    return backend.get_user(-1)


class TestDjangoAuth0(TestCase):
    """ Test Auth0Backend """

    def setUp(self):
        self.backend = Auth0Backend()
        self.user = User.objects.create_user(username='user', email='email@email.com')

    def test_existing_user_returned(self):
        """ Test if get user returns a user if it exists in database """
        self.assertIsNotNone(self.backend.get_user(self.user.pk))

    def test_exception_raised_when_user_not_found(self):
        """ Test if get user returns a user if it exists in database """
        self.assertRaises(User.DoesNotExist, self._get_user)

    def _get_user(self):
        return _get_user(self.backend)
