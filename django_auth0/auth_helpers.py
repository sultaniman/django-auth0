# -*- coding: utf-8 -*-
import json
import requests
import logging

from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.shortcuts import redirect
from .utils import get_config

logger = logging.getLogger(__name__)


def process_login(request):
    """
    Default handler to login user
    :param request: HttpRequest
    """
    code = request.GET.get('code', '')
    config = get_config()
    json_header = {'content-type': 'application/json'}
    token_url = 'https://%s/oauth/token' % config['AUTH0_DOMAIN']

    token_payload = {
        'client_id': config['AUTH0_CLIENT_ID'],
        'client_secret': config['AUTH0_SECRET'],
        'redirect_uri': config['AUTH0_CALLBACK_URL'],
        'code': code,
        'grant_type': 'authorization_code'
    }

    token_info = requests.post(token_url,
                               data=json.dumps(token_payload),
                               headers=json_header).json()

    url = 'https://%s/userinfo?access_token=%s'
    user_url = url % (config['AUTH0_DOMAIN'],
                      token_info.get('access_token', ''))
    logger.info(user_url)

    try:
        user_info = requests.get(user_url).json()
    except json.decoder.JSONDecodeError as e:
        logger.warning(e)
        return HttpResponse('invalid request (json decode error)', status=400)

    logger.info(user_info)

    # We're saving all user information into the session
    request.session['profile'] = user_info
    user = authenticate(**user_info)

    if user:
        login(request, user)
        logger.info(f'authenticated user: {user}')
        return redirect(config['AUTH0_SUCCESS_URL'])

    logger.warning(f'no user found for request: {request}')

    return HttpResponse(status=400)
