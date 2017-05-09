# -*- coding: utf-8 -*-
from auth0.v3.authentication import GetToken
from django.conf import settings


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
