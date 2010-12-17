# -*- coding: utf-8 -*-


"""

Developer
==================================================

Create user & developer

>>> _username = u"test user"
>>> _email = u"test@test.com"
>>> _password = u"this is password"

>>> _profile = models_develper.Profile.objects.get_or_create(
...	    _username,
...	    _email,
...	    _password,
...	)

>>> _profile.user.username == _username
True
>>> _profile.user.email == _email
True
>>> _profile.user.check_password(_password, )
True
>>> _profile.user.is_active
True

Create anonymous user

>>> _username_anonymous = u"a" + _username
>>> _anonymous = models_develper.Profile.objects.get_or_create(
...	    _username_anonymous,
...	    u"a" + _email,
...	    _password,
...	    is_anonymous=True,
...	)

Anonymous user does not have `models_developer.Profile`, Anonymous user does
not have password, so can not login to system.

>>> _user_anonymous = models_auth.User.objects.get(username=_username_anonymous, )

>>> _user_anonymous.is_active
False
>>> _user_anonymous.check_password(_password, )
False


"""

from django.contrib.auth import models as models_auth
import models as models_develper

if __name__ == "__main__" :
    import doctest
    doctest.testmod()






