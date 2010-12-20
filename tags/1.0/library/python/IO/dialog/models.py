# -*- coding: utf-8 -*-

from django.db import models, IntegrityError
from django.db.models import manager, Q
from django.contrib.auth import models as models_auth
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.contenttypes import models as models_contenttypes
from django.utils.copycompat import deepcopy

from django_modules.db.models.query import translate_query

from IO.common import models as models_common
from IO.developer import models as models_developer

MESSAEG_TYPES = (
    ("email", "Email", ),
    ("im", "Instant Messenger", ),
    ("web", "Web", ),
)

LABEL_INBOX = u"Inbox"

class LabelManager (manager.Manager, ) :
    def get_or_create (self, name, ) :
        try :
            return super(LabelManager, self).get_or_create(name=name, )
        except IntegrityError :
            return (self.get(name=name, ), False, )

class Label (models.Model, ) :
    objects = LabelManager()

    name = models.CharField(max_length=100, unique=True, )

    def __unicode__ (self, ) :
        return u"%s" % self.name

class MessageManager (manager.Manager, ) :
    def filter_by_users (self, *users) :
        return self.filter(
            Q(receiver__in=users,) | Q(receivers__in=users,) | Q(sender__in=users, ),
        )

    def filter_by_profile (self, profile, ) :
        _users = list(profile.users.all()) + [profile.user, ]
        return self.filter_by_users(*_users)

class Message (models_common.BaseJoin, models_common.ReferenceTag, ) :
    objects = MessageManager()

    class Meta :
        ordering = ("time_sent", "time_added", )

    time_added = models.DateTimeField(auto_now_add=True)

    uid = models.CharField(max_length=255, unique=True, )

    sender = models.ForeignKey(models_auth.User, related_name="messages_sent",
        blank=True, null=True, )
    sender_address = models.CharField(max_length=200, blank=True, null=True, )

    receiver = models.ForeignKey(models_auth.User, related_name="messages_receiver", )
    receiver_address = models.TextField(blank=True, null=True, )
    receivers = models.ManyToManyField(models_auth.User, related_name="messages_receivers", )
    receivers_address = models.TextField(blank=True, null=True, )

    subject = models.TextField(blank=True, null=True, )
    content = models.TextField(blank=True, null=True, )
    content_type = models.CharField(max_length=50, default="text/plain", )

    message_type = models.CharField(choices=MESSAEG_TYPES, max_length=6, )

    parent_top = models.ForeignKey("self", blank=True, null=True, related_name="all_children", )
    parent = models.ForeignKey("self", blank=True, null=True, related_name="children", )
    parent_uid = models.CharField(max_length=255, blank=True, null=True, )

    reply_to = models.CharField(max_length=200, blank=True, null=True, )

    time_sent = models.DateTimeField()

    watchers = models.ManyToManyField(models_auth.User, related_name="dialog_watchers", )

    def __unicode__ (self, ) :
        return u"pk:%d" % self.pk

    def _get_reference_tag (self, ) :
        return u"dialog:%s" % (
            self.parent_top.oid.hex,
        )

    @property
    def is_top (self, ) :
        return self == self.parent_top

    def get_children (self, ) :
        for i in self.__class__.objects.filter(parent=self, ).order_by("time_sent") :
            yield i
            for j in i.get_children() :
                yield j

    @property
    def dialog (self, ) :
        return self.__class__.objects.filter(
            parent_top=self.parent_top, ).order_by("time_sent", )

    def get_participants (self, q=None, ) :
        _q = Q(profiles__isnull=False, )
        if q :
            _q = _q & q

        _q0s = (
            {"messages_sent__parent_top": self.parent_top, },
            {"messages_receiver__parent_top": self.parent_top, },
            {"messages_receivers__parent_top": self.parent_top, },
        )

        _users = list()
        for i in _q0s :
            _users.extend(
                models_auth.User.objects.filter(_q & Q(**i), ),
            )

        return set(_users, )

    @property
    def count_messages (self, ) :
        return self.parent_top.all_children.count()

    def update_parent (self, parent, ) :
        self.parent = parent
        self.parent_top = parent.parent_top

        self.save()

        self.__class__.objects.filter(
            parent_top=self,
        ).exclude(pk=self.pk, ).update(parent_top=self.parent_top, )

        return

    def save (self, *a, **kw) :
        _created = not self.pk

        super(Message, self).save(*a, **kw)

        if _created :
            if not self.parent :
                _parent_top = self
            else :
                _parent_top = self.parent.parent_top

            self.parent_top = _parent_top
            self.save()

        return

class Payload (models.Model, ) :
    class Meta :
        unique_together = ("message", "file", )

    message = models.ForeignKey(Message, related_name="payloads", )

    file = models.FileField(upload_to="message_payload/%Y/%m/%d", )
    filename = models.CharField(max_length=400, )
    mimetype = models.CharField(max_length=200, blank=True, null=True, )

    def __unicode__ (self, ) :
        return "%s (%s)" % (self.filename, self.message, )

class BaseProfileMessageManager (manager.Manager, ) :
    def get_by_message (self, user_or_profile, message, ) :
        if not isinstance(user_or_profile, models_developer.Profile, ) :
            user_or_profile = models_developer.Profile.objects.get_by_user(user_or_profile, )

        return self.get(profile=user_or_profile, message=message, )

class BaseProfileMessage (models.Model, ) :
    objects = BaseProfileMessageManager()

    class Meta :
        abstract = True
        unique_together = ("profile", "message", )
        ordering = ("-time_updated", "message__time_sent", )

    profile = models.ForeignKey(models_developer.Profile, )
    message = models.ForeignKey(Message, )

    time_updated = models.DateTimeField(auto_now_add=True, )

    is_starred = models.BooleanField(default=False, )
    labels = models.ManyToManyField(Label, )

    @property
    def parent_top (self, ) :
        if isinstance(self, ProfileMessageTop, ) :
            return self

        return ProfileMessageTop.objects.get_or_create(
            profile=self.profile,
            message=self.message.parent_top,
        )[0]

    @property
    def is_top (self, ) :
        return self.message.is_top

    @property
    def is_archived (self, ) :
        return self.parent_top.labels.filter(name=LABEL_INBOX, ).count() < 1

    def archive (self, ) :
        self.parent_top.labels.remove(Label.objects.get_or_create(name=LABEL_INBOX, )[0], )
        return

    def unarchive (self, ) :
        if self.parent_top.labels.filter(name=LABEL_INBOX, ).count() > 0 :
            return

        self.parent_top.labels.add(Label.objects.get_or_create(name=LABEL_INBOX, )[0], )

class ProfileMessageTop (BaseProfileMessage, ) :
    """
    Only cover the parent_top message.
    """

    is_read = models.BooleanField(default=False, )

    @classmethod
    def signal_callback_post_save_message (cls, *a, **kw) :
        if kw.get("action") and not kw.get("action").startswith("post_") :
            return

        _instance = kw.get("instance")
        if not _instance.parent_top :
            return

        _instance = _instance.parent_top

        _q = Q(profiles__isnull=False, )
        _qs = _instance.get_participants(_q, )
        for _user in _qs :
            _profile = models_developer.Profile.objects.get_by_user(_user, )
            (_um, _created, ) = cls.objects.get_or_create(
                profile=_profile, message=_instance, )

            if _instance.dialog.count() > 1 :
                _qs = cls.objects.filter(
                    profile=_profile,
                    message__parent_top=_instance,
                ).exclude(message=_instance, ).distinct()
                if _qs.count() > 0 :
                    _qs.delete()

            _um.unarchive()
            if not _created :
                _um.is_read = False
                _um.save()

        return

    def save (self, *a, **kw) :
        if not self.message.is_top :
            raise RuntimeError(u"`message` must be top message.", )

        return super(ProfileMessageTop, self).save(*a, **kw)

    def set_labels (self, labels, ) :
        _is_archived = self.is_archived
        self.labels = labels

        if not _is_archived :
            self.unarchive()

    def set_is_starred (self, ) :
        self.is_starred = True in [i.is_starred for i in ProfileMessage.objects.filter(
            profile=self.profile, message__parent_top=self.message, )]
        self.save()

class ProfileMessage (BaseProfileMessage, ) :
    @classmethod
    def signal_callback_post_save_labels (cls, *a, **kw) :
        _instance = kw.get("instance")
        if kw.get("action") != "post_add" :
            return

        _labels = Label.objects.filter(
            profilemessage__profile=_instance.profile,
            profilemessage__message__parent_top=_instance.message.parent_top,
        ).distinct()

        _instance.parent_top.set_labels(_labels, )

    @classmethod
    def signal_callback_post_save (cls, *a, **kw) :
        _instance = kw.get("instance")
        _parent_top = _instance.parent_top
        _parent_top.save()

        _parent_top.set_is_starred()

class BaseConnectedMessage (models.Model, ) :
    class Meta :
        abstract = True

    time_connected = models.DateTimeField(auto_now_add=True, )

    def __unicode__ (self, ) :
        return u"ConnectedMessage(%s.%s): %s" % (
            self._meta.app_label,
            self._meta.module_name,
            self.message,
        )

class ConnectedMessageManager (manager.Manager, ) :
    """
    It will totally return the Message model queryset.
    """

    def get_query_set (self, ) :
        return Message.objects.filter().distinct()

    def _translate_queries (self, *a, **kw) :
        if not kw and len(a) < 2 and isinstance(a[0], Q, ) :
            _query = deepcopy(a[0])
        else :
            _query = Q(*a, **kw)

        _query_new = deepcopy(_query, )
        _query_new.children = list()

        _content_object = None

        for i in range(len(_query.children, ), ) :
            _q = _query.children[i]
            if isinstance(_q, Q, ) :
                _q = self._translate_queries(_q, )
            elif isinstance(_q, tuple, ) :
                pass
            else : # it must be content_object
                _content_object = _q
                continue

            _query_new.children.append(_q, )

        if _content_object :
            _query_new = self._translate_query(_content_object, _query_new, )

        return _query_new

    def _translate_query (self, content_object, q, ) :
        """
        It works by atomic way by content_object.
        """
        _content_object = None
        if type(content_object, ) in (str, unicode, ) :
            (_app_label, _module_name, ) = content_object.split(".")
        else :
            _content_object = content_object
            (_app_label, _module_name, ) = (content_object._meta.app_label,
                content_object._meta.module_name, )

        _model = models.get_model(_app_label, _module_name, )
        _message = models.get_model(_app_label, "message", )
        if not _model or not _message :
            raise RuntimeError(u"Unregistered connected message model.", )

        return _message.objects.get_query_set_for_message(_content_object, q, )

    def filter (self, *a, **kw) :
        return super(ConnectedMessageManager, self).filter(
            self._translate_queries(*a, **kw)
        )

    def exclude (self, *a, **kw) :
        return super(ConnectedMessageManager, self).exclude(
            self._translate_queries(*a, **kw)
        )

    def get (self, *a, **kw) :
        return super(ConnectedMessageManager, self).get(
            self._translate_queries(*a, **kw)
        )

    def get_or_create (self, message, content_object, ) :
        _ct = models_contenttypes.ContentType.objects.get_for_model(content_object, )
        _model = models.get_model(_ct.app_label, "message", )
        return _model.objects.get_or_create(message, content_object, )

class ConnectedMessage (models.Model, ) :
    objects = ConnectedMessageManager()

##################################################
# Signals
models.signals.m2m_changed.connect(
    ProfileMessageTop.signal_callback_post_save_message,
    sender=Message.receivers.through,
)
models.signals.m2m_changed.connect(
    ProfileMessage.signal_callback_post_save_labels,
    sender=ProfileMessage.labels.through,
)
models.signals.post_save.connect(
    ProfileMessageTop.signal_callback_post_save_message,
    sender=Message,
)
models.signals.post_save.connect(
    ProfileMessage.signal_callback_post_save,
    sender=ProfileMessage,
)

