# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

UserModel = get_user_model()


class Auth0Backend(object):
    def authenticate(self, email=None, nickname=None, **kwargs):
        """
        Auth0 return a dict which contains the following fields
        :param email: user email
        :param nickname: username
        :param kwargs: kwargs
        :return: user
        """
        if nickname and email:
            try:
                return UserModel.objects.get(email__iexact=email,
                                             username__iexact=nickname)
            except UserModel.DoesNotExist:
                return UserModel.objects.create(email=email,
                                                username=nickname)

        raise ValueError(_('Username or email can\'t be blank'))

    def get_user(self, user_id):
        try:
            return UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
