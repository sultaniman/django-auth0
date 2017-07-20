import requests
from auth0.v3.management import Auth0
from django.conf import settings
from logging import getLogger

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .utils import TokenManager, generate_auth0_user_patch_request, get_auth0_group_by_name

T_MANAGER = TokenManager()

logger = getLogger(__name__)


def update_auth0_group(sender, instance, **kwargs):
    """ Create Auth0 group when a group is added locally """
    logger.debug('group signal triggered')
    token = T_MANAGER.get_token(audience='urn:auth0-authz-api')
    group = get_auth0_group_by_name(instance.name, token)

    if group:
        return
    else:
        logger.warning('Propagating group "{instance_name}" to Auth0'.format(
            instance_name=instance.name
        ))
        r = requests.post(
            settings.AUTH0_AUTHORIZATION_API + '/groups',
            json={
                'name': instance.name,
                'description': '(no description provided)'
            },
            headers={
                'Authorization': 'Bearer ' + token
            }
        )
        assert r.status_code == 200


def update_auth0_groups(sender, instance, model, action, pk_set, **kwargs):
    """
    Update users's group membership in Auth0 when updated locally.

    DO NOT register this function if not using a user model that is wired to
    Django's groups.
    """
    # TODO gut this filter logic and replace with kwargs on connector setup
    if model != Group:
        return
    if type(instance) != get_user_model():
        return

    user_id = instance.username.replace('-', '|')

    group_names = Group.objects.filter(
        pk__in=pk_set
    ).values_list('name', flat=True)
    group_ids = list()
    for name in group_names:
        group_ids.append(
            get_auth0_group_by_name(
                name,
                T_MANAGER.get_token(audience='urn:auth0-authz-api')
            )['_id'])

    if action == 'pre_add':
        f = 'patch'
    elif action == 'pre_remove':
        f = 'delete'
    else:
        return

    for id_ in group_ids:
        token = T_MANAGER.get_token(audience='urn:auth0-authz-api')
        r = getattr(requests, f)(
            f'{settings.AUTH0_AUTHORIZATION_API}/groups/{id_}/members',
            json=[user_id],
            headers={
                'Authorization': f'Bearer {token}'
            }
        )
        # move outside function
        acceptable_statuses = {200, 204}
        if f == 'delete':
            acceptable_statuses.add(202)
        try:
            assert r.status_code in acceptable_statuses,\
                f'bad status ({r}) when adding user to group'
        except AssertionError as err:
            if 'indexOf' in r.text and f == 'delete':
                # empty group
                continue
            raise err


def update_auth0_user(_, instance, **kwargs):
    user, *store = instance.username.split('-')
    if len(store) < 1:
        logger.debug("got what seems to be a non-interactive client ID:", user)
        return
    elif len(store) > 1:
        logger.error("got user of unkown type!")
    else:
        # rebuild id
        store = store[0]
        user = user + '|' + store
        assert store == 'auth0', f'Auth0 user store "{store}" unsupported.'
    api = Auth0(settings.AUTH0_DOMAIN, T_MANAGER.get_token())
    patch = generate_auth0_user_patch_request(instance)
    api.users.update(user, patch)
