# -*- coding: utf-8 -*-
from auth0.v3.authentication import GetToken
from django.conf import settings


AUTH0_FIELD_MAPPING = {
    'user_metadata.first_name': 'first_name',
    'user_metadata.last_name': 'last_name',
    'email': 'email'
}

USER_AUTH0_FIELD_MAPPING = {v: k for k, v in AUTH0_FIELD_MAPPING.items()}


def get_config():
    """ Collects AUTH0_* configurations """
    return {
        'AUTH0_CLIENT_ID': settings.AUTH0_CLIENT_ID,
        'AUTH0_SECRET': settings.AUTH0_SECRET,
        'AUTH0_DOMAIN': settings.AUTH0_DOMAIN,
        'AUTH0_CALLBACK_URL': settings.AUTH0_CALLBACK_URL,
        'AUTH0_SUCCESS_URL': settings.AUTH0_SUCCESS_URL,
    }


def get_token(*, a0_config: dict=None, audience=None) -> str:
    """ 
    Generate an authentication connection to Auth0 service

    :param a0_config: Auth0 configuration parameters
    :param audience: Token audience (defaults to f'https://{domain}/api/v2/') 
    """

    if not audience:
        audience = 'https://%s/api/v2/' % a0_config["AUTH0_DOMAIN"]

    r = GetToken(a0_config['AUTH0_DOMAIN'])
    token = r.client_credentials(
        a0_config['AUTH0_CLIENT_ID'],
        a0_config['AUTH0_SECRET'],
        audience
    )
    return token['access_token']


def map_auth0_attrs_to_user(user_object, **kwargs):
    modified = False
    for attr_path, local_field_name in AUTH0_FIELD_MAPPING.items():
        path = attr_path.split('.')
        v = kwargs.get(path.pop(0))
        for k in path:
            try:
                v = v.get(k)
            except Exception as err:
                print(err)
                break
            if not v:
                break
        else:
            if getattr(user_object, local_field_name) != v:
                setattr(user_object, local_field_name, v)
                modified = True
    return modified


def map_user_attrs_to_auth0(user: dict, instance):
    user_updates = dict()
    for attr, mapping in USER_AUTH0_FIELD_MAPPING.items():
        path = mapping.split('.')
        v = getattr(instance,
        v = kwargs.get(path.pop(0))
        for k in path:
            try:
                v = v.get(k)
            except Exception as err:
                print(err)
                break
            if not v:
                break
        else:
            if getattr(user_object, local_field_name) != v:
                setattr(user_object, local_field_name, v)
                modified = True
    return modified
