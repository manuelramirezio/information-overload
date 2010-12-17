# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db.models import get_model

from django_modules.db.models.fields import UUIDField

from utils import parse_join_email, get_object_from_join_email

CHOICES_CONFIGURATION = (
    ("str", "String", ),
    ("int", "Integer", ),
    #("list", "List", ),
    #("tuple", "Tuple", ),
    #("dict", "dict", ),
)

class Configuration (models.Model, ) :
    class Meta :
        unique_together = ("name", )

    name = models.CharField(max_length=200, )
    value = models.TextField()
    value_type = models.CharField(
        max_length=10, choices=CHOICES_CONFIGURATION, default="str", )

    def __unicode__ (self, ) :
        return u"%s: %s" % (self.name, self.value, )

class BaseJoin (models.Model, ) :
    class Meta :
        abstract = True

    oid = UUIDField(version=1, auto=True, )

    @property
    def join_email (self, ) :
        return ("%s+%%s@%s" % settings.EMAIL_IO_SERVICE_PARTED) % self._get_join_oid()

    def _get_join_oid (self, ) :
        return "%s-%s-%s" % (
            self._meta.app_label,
            self._meta.module_name,
            self.oid.hex,
        )

class ReferenceTag (models.Model, ) :
    class Meta :
        abstract = True

    @property
    def reference_tag (self, ) :
        return self._get_reference_tag()


