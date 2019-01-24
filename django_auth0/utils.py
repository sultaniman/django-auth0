# -*- coding: utf-8 -*-
import datetime
from typing import Optional

import requests
from auth0.v3.authentication import GetToken
from django.conf import settings
from logging import getLogger

AUTH0_FIELD_MAPPING = {
    'user_metadata.first_name': 'first_name',
    'user_metadata.last_name': 'last_name',
    'email': 'email'
}

USER_AUTH0_FIELD_MAPPING = {v: k for k, v in AUTH0_FIELD_MAPPING.items()}

logger = getLogger(__name__)


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


class TokenManager(object):
    # in order to simplify logic, tokens are expired early
    lifetime = datetime.timedelta(hours=23)
    __cache = dict()

    def __init__(self):
        pass

    def get_token(self, audience: str=None) -> str:
        now = datetime.datetime.now()
        token = self.__cache.get(audience)
        if token:
            if token['expires'] > now:
                logger.debug('{audience} token cache hit'.format(
                    audience=audience
                ))
                token['hits'] += 1
                return token['access_token']
            logger.debug('{audience} token expired ({hits} hits)'.format(
                audience=audience,
                hits=token["hits"],
            ))
        access_token = get_token(
            a0_config=get_config(),
            audience=audience
        )
        self.__cache[audience] = {
            'expires': now + self.lifetime,
            'access_token': access_token,
            'hits': 0
        }
        return access_token


def get_auth0_group_by_name(group_name: str, token: str) -> Optional[dict]:
    """
    Get an Auth0 group by name
    
    :return: group, if found, else none
    """
    r = requests.get(
        settings.AUTH0_AUTHORIZATION_API + '/groups',
        headers={
            'Authorization': 'Bearer ' + token
        }
    )
    assert r.status_code == 200, \
        'bad status when creating the group in Auth0: ' + str(r)
    j = r.json()
    assert len(j['groups']) == j['total']  # TODO pagination

    for g in j['groups']:
        if g['name'] == group_name:
            return g

    return None


def nested_set(dic: dict, keys: list, value):
    """ Set a nested dict value given a list of indices """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def map_auth0_attrs_to_user(user_object, **kwargs):
    """ Update provided user with attributes from the Auth0 API """
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


def generate_auth0_user_patch_request(instance, patch=None) -> dict:
    """
    Generate the body of a PATCH request to update a user
    
    :param instance: User object
    :param patch: Base request dict that will be extended and overridden
    :return: Dict that may be serialized and sent to Auth0 as the body of the request
     """
    if not patch:
        patch = {}
    for attr, mapping in USER_AUTH0_FIELD_MAPPING.items():
        path = mapping.split('.')
        v = getattr(instance, attr)
        nested_set(patch, path, v)
    return patch
