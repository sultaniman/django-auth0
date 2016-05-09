#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `django-auth0` authentication backend.
"""
from django.test import TestCase
from django_auth0.context_processors import auth0


class TestDjangoAuth0ContextProcessor(TestCase):
    """ Test Auth0Backend ContextProcessor """

    def test_context_processor(self):
        """ It returns dict with settings """
        config = auth0(None)
        self.assertTrue(len(config.keys()) > 0)
        self.assertTrue(type(config) == dict)
