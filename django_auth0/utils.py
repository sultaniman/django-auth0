# -*- coding: utf-8 -*-
from django.conf import settings
from .settings import AUTH0_CALLBACK_URL


def get_config():
    return {
        'AUTH0_CLIENT_ID': settings.AUTH0_CLIENT_ID,
        'AUTH0_SECRET': settings.AUTH0_SECRET,
        'AUTH0_DOMAIN': settings.AUTH0_DOMAIN,
        'AUTH0_CALLBACK_URL': AUTH0_CALLBACK_URL
    }
