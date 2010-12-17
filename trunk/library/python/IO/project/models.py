# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import manager, Q
from django.contrib.auth import models as models_auth

from django_modules.db.models.query import translate_query

from IO.common import models as models_common
from IO.dialog import models as models_dialog

class Item (models_common.ReferenceTag, ) :
    class Meta :
        verbose_name = u"Project"

    name = models.CharField(max_length=100, )
    code = models.CharField(max_length=100, unique=True, )

    author = models.ForeignKey(models_auth.User, db_index=True, )
    time_added = models.DateTimeField(auto_now_add=True, )

    configuration = models.ManyToManyField(
        models_common.Configuration, blank=True, null=True, )

    def __unicode__ (self, ) :
        return u"%s (code: %s)" % (self.name, self.code, )

    def _get_reference_tag (self, ) :
        return u"project:%s" % self.code

    @property
    def participants (self, ) :
        return [self.author, ]

class MessageManager (manager.Manager, ) :
    def _translate (self, q, ) :
        _q = list(q[:])
        _q[0] = "project_message__%s" % _q[0]

        return tuple(_q, )

    def get_query_set_for_message (self, content_object, *a, **kw) :
        _q = Q(*a, **kw)
        if content_object :
            _q = _q & Q(project=content_object, )

        return translate_query(
            _q,
            func=self._translate,
        )

    def get_or_create (self, message, content_object, ) :
        return super(MessageManager, self).get_or_create(
            message=message, project=content_object, )

class Message (models_dialog.BaseConnectedMessage, ) :
    objects = MessageManager()

    class Meta :
        unique_together = ("project", "message", )

    message = models.ForeignKey(models_dialog.Message, related_name="project_message", )
    project = models.ForeignKey(Item, )

