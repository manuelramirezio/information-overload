# -*- coding: utf-8 -*-

import datetime

from django.db import models
from django.db.models import manager, Q, ObjectDoesNotExist
from django.contrib.auth import models as models_auth
from django.core.urlresolvers import reverse

DEFAULT_PROFILE_PICTURE = u"image/unknown.png"

class ProfileManager (manager.Manager, ) :
    def get_by_user (self, user, ) :
        _qs = user.profiles.all()
        if _qs.count() < 1 :
            return None

        return _qs[0]

    def get_or_create (self,
            username, email, password=None, is_anonymous=False, nickname=None, ) :

        # get profile.
        try :
            return self.get(user__email=email, )
        except ObjectDoesNotExist :
            pass

        (_user, _created, ) = self.get_or_create_user(
            username,
            email,
            password=not is_anonymous and password or None,
        )
        if not _created :
            return FakeProfile(_user, )

        _user.is_active = not is_anonymous
        if is_anonymous and nickname :
            _user.first_name = nickname

        _user.save()

        if is_anonymous :
            return FakeProfile(_user, )

        _profile = self.create(
            user=_user,
            nickname = nickname and nickname or _user.username
        )
        _profile.users.add(_user, )

        return _profile

    def get_or_create_user (self, username, email, password=None, ) :
        _qs = models_auth.User.objects.filter(email=email, )
        if _qs.count() > 0 :
            return (_qs[0], False, )

        _n = 1
        _username = username[:30]
        while self.filter(user__username=_username, ).count() > 0 :
            _username = u"%s (%d)" % (username[:30], _n, )
            _n += 1

        return (
            models_auth.User.objects.create_user(
                _username,
                email,
                password=password,
            ),
            True,
        )

class FakeProfile (models.Model, ) :
    def __init__ (self, user, ) :
        self.user = user

class Profile (models.Model, ) :
    objects = ProfileManager()

    class Meta :
        pass

    user = models.OneToOneField(models_auth.User, related_name="profile", unique=True, )
    users = models.ManyToManyField(models_auth.User, related_name="profiles", )

    jid = models.EmailField(max_length=200, blank=True, null=True, db_index=True, )
    picture = models.ImageField(upload_to="profile_picture", blank=True, null=True, )

    nickname = models.CharField(max_length=200, blank=True, null=True, )

    def __unicode__ (self, ) :
        return u"%s <%s>" % (self.user.username, self.user.email, )

    @property
    def profile_picture (self, ) :
        if not self.picture :
            return reverse("static_media", kwargs=dict(
                path=DEFAULT_PROFILE_PICTURE, ),
            )

        return self.picture.url

    @property
    def projects (self, ) :
        from IO.project import models as models_project
        return models_project.Item.objects.filter(
            version_control__revision__author=self.user,
        ).distinct()

    @property
    def aliases (self, ) :
        return self.users.all().order_by("date_joined", )

class ConfirmEmail (models.Model, ) :
    key = models.CharField(max_length=45, unique=True, )
    profile = models.ForeignKey(Profile, )
    email = models.EmailField()
    time_added = models.DateTimeField(auto_now_add=True, )

    def is_valid (self, ) :
        return self.time_added > (datetime.datetime.now() - datetime.timedelta(days=1, ))



