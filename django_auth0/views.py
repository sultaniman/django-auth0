# -*- coding: utf-8 -*-
from .auth_helpers import process_login


def auth_callback(request):
    return process_login(request)
