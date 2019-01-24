# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from .utils import AUTH0_FIELD_MAPPING, map_auth0_attrs_to_user

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
        # check that each auth0 key is present in kwargs
        for key in AUTH0_USER_INFO_KEYS:
            if key not in kwargs:
                # End the authentication attempt if this is not an Auth0
                # payload.
                return

        user_id = kwargs.get('user_id', None)

        if not user_id:
            raise ValueError(_('user_id can\'t be blank!'))

        # The format of user_id is
        #    {identity provider id}|{unique id in the provider}
        # The pipe character is invalid for the django username field
        # The solution is to replace the pipe with a dash
        username = user_id.replace('|', '-')

        # sentinel value for user modification or creation
        modified = False

        try:
            u = UserModel.objects.get(username__iexact=username)
        except UserModel.DoesNotExist:
            u = UserModel(username=username)
            u.set_unusable_password()
            modified = True

        modified = modified | map_auth0_attrs_to_user(u, **kwargs)

        authorization = kwargs.get('authorization')
        if authorization:
            for role in authorization['roles']:
                try:
                    local_value = getattr(u, role)
                    if type(local_value) != bool:
                        raise NotImplementedError()
                    if not local_value:
                        setattr(u, role, True)
                        modified = True
                except Exception as err:
                    print(err)

        if modified:
            u.save()

        return u

    # noinspection PyProtectedMember
    def get_user(self, user_id):
        """
        Primary key identifier
        It is better to raise UserModel.DoesNotExist
        :param user_id:
        :return: UserModel instance
        """
        return UserModel._default_manager.get(pk=user_id)
