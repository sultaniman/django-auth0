=============================
django-auth0
=============================

.. image:: https://badge.fury.io/py/django-auth0.png
    :target: https://badge.fury.io/py/django-auth0

.. image:: https://travis-ci.org/imanhodjaev/django-auth0.png?branch=master
    :target: https://travis-ci.org/imanhodjaev/django-auth0

Django Auth0 authentication background

Documentation
-------------

The full documentation is at https://django-auth0.readthedocs.org.

Quickstart
----------

Install django-auth0::

    pip install django-auth0

Add `django_auth0` to `INSTALLED_APPS`::

Add `django_auth0.auth_backend.Auth0Backend` to `AUTHENTICATION_BACKENDS`::
.

.. code-block:: python

    AUTHENTICATION_BACKENDS = [
        "django_auth0.auth_backend.Auth0Backend",
        "django.contrib.auth.backends.ModelBackend"
    ]


Add Auth0 client side JavaScript and initialize it::
.

.. code-block:: python

    <script src="https://cdn.auth0.com/js/lock-8.2.min.js"></script>
    <script>
      var lock = new Auth0Lock('{{ AUTH0_CLIENT_ID }}', '{{ AUTH0_DOMAIN }}');


      lock.show({
          icon: 'ICON_URL',
          container: 'CONTAINER_ELEMENT',
          callbackURL: 'YOUR_FULL_CALLBACK_URL',
          responseType: 'code',
          authParams: {
              scope: 'openid profile'
          }
      });
    </script>

Options::

1. `AUTH0_CLIENT_ID` - Auth0 client app id,
2. `AUTH0_SECRET` - Auth0 app secret,
3. `AUTH0_DOMAIN` - Auth0 subdomain `YOU_APP.auth0.com`.
4. `AUTH0_CALLBACK_URL` - Auth0 callback url, it should be url name not path.

Overriding callback view::
Default callback view looks like this so you can always write your own and
set `AUTH0_CALLBACK_URL` to your custom view it should be url name.

.. code-block:: python

    def process_login(request):
        """
        Default handler to login user
        :param request:
        :return:
        """
        code = request.GET.get('code', None)
        json_header = {'content-type': 'application/json'}
        token_url = 'https://%s/oauth/token' % settings.AUTH0_DOMAIN

        token_payload = {
            'client_id': settings.AUTH0_CLIENT_ID,
            'client_secret': settings.AUTH0_SECRET,
            'redirect_uri': reverse(settings.AUTH0_CALLBACK_URL),
            'code': code,
            'grant_type': 'authorization_code'
        }

        token_info = requests.post(token_url,
                                   data=json.dumps(token_payload),
                                   headers=json_header).json()

        url = 'https://%s/userinfo?access_token=%s'
        user_url = url % (settings.AUTH0_DOMAIN, token_info['access_token'])
        user_info = requests.get(user_url).json()

        # We're saving all user information into the session
        request.session['profile'] = user_info
        user = authenticate(**user_info)

        if user:
            login(request, user)
            return redirect(settings.AUTH0_CALLBACK_URL)

        return HttpResponse(status=400)


Features
--------

TODO
--------

* Improve tests


Running Tests
--------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install -r requirements-test.txt
    (myenv) $ python runtests.py

Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-pypackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
