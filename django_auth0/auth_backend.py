# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

UserModel = get_user_model()


class Auth0Backend(object):
    def authenticate(self, email=None, username=None, **kwargs):
        """
        Auth0 return a dict which contains the following fields
        :param email: user email
        :param username: username
        :param kwargs: kwargs
        :return: user
        """
        if username and email:
            try:
                return UserModel.objects.get(email__iexact=email,
                                             username__iexact=username)
            except UserModel.DoesNotExist:
                return UserModel.objects.create(email=email,
                                                username=username)

        raise ValueError(_('Username or email can\'t be blank'))

    def get_user(self, user_id):
        """
        Primary key identifier
        It is better to raise UserModel.DoesNotExist
        :param user_id:
        :return: UserModel instance
        """
        return UserModel._default_manager.get(pk=user_id)
