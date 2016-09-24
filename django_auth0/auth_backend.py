# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _


UserModel = get_user_model()

# user profile keys that are always present as specified by
# https://auth0.com/docs/user-profile/normalized#normalized-user-profile-schema
AUTH0_USER_INFO_KEYS = [
    'name',
    'nickname',
    'picture',
    'user_id',
]


class Auth0Backend(object):
    def authenticate(self, **kwargs):
        """
        Auth0 return a dict which contains the following fields
        :param kwargs: user information provided by auth0
        :return: user
        """
        is_auth0 = True

        # check that each auth0 key is present in kwargs
        for key in AUTH0_USER_INFO_KEYS:
            if key not in kwargs:
                is_auth0 = False
                break

        # End the authentication attempt if this is not an auth0 payload
        if is_auth0 is False:
            return None

        user_id = kwargs.get('user_id')

        if user_id is None:
            raise ValueError(_('user_id can\'t be blank!'))

        # The format of user_id is
        #    {identity provider id}|{unique id in the provider}
        # The pipe character is invalid for the django username field
        # The solution is to replace the pipe with a dash
        username = user_id.replace('|', '-')

        try:
            user = UserModel.objects.get(username__iexact=username)
        except UserModel.DoesNotExist:
            user = UserModel.objects.create(username=username)

        return user

    # noinspection PyProtectedMember
    def get_user(self, user_id):
        """
        Primary key identifier
        It is better to raise UserModel.DoesNotExist
        :param user_id:
        :return: UserModel instance
        """
        return UserModel._default_manager.get(pk=user_id)
