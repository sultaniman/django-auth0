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

Add Auth0 client side JavaScript and initialize it::

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
4. `AUTH0_CALLBACK_URL` - Auth0 callback url.


Features
--------

TODO
--------

* Write tests


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
