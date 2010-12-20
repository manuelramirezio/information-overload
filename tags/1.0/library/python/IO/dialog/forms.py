# -*- coding: utf-8 -*-

import re, uuid, StringIO, base64

from django import forms
from django.db.models import ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile

from spikeekips import _email

from IO.common import utils as utils_common
from IO.developer import models as models_developer
from IO.dialog import models as models_dialog, utils as utils_dialog

def get_model (message_type, ) :
    return globals().get("%sHandler" % message_type.title(), )

class BaseHandler (object, ) :
    def save (self, *a, **kw) :
        pass

class EmailHandler (BaseHandler, ) :
    def __init__ (self, message, ) :
        self._message = message

    def save (self, ) :
        try :
            _email_message = _email.Message.from_string(self._message, )
            if not _email_message.is_valid() :
                raise TypeError
        except TypeError :
            raise forms.ValidationError(u"Invalid email message.", )

        # check whether this message is already taken or not by using `Message-Id`
        _message_id = utils_dialog.normalize_message_id(
            _email_message.get_header("message-id"), )

        _qs = models_dialog.Message.objects.filter(uid=_message_id, )
        if _qs.count() > 0 :
            return (_qs[0], False, ) # (<message>, <created>, )

        # analyze email
        _data = dict(
            uid         = _email_message.get_header("message-id"),
            time_sent   = _email_message.get_header("date"),
            subject     = _email_message.get_header("subject"),
        )

        # sender
        _sender = None
        _sender_address = _email_message.get_header("from")[0]
        _sender = models_developer.Profile.objects.get_or_create(
            str(uuid.uuid1(), ),
            email=_sender_address[1],
            is_anonymous=True,
            nickname=_sender_address[0],
        ).user

        _data["sender_address"] = _sender_address[1]
        _data["sender"] = _sender

        # receiver & receivers
        _receiver_address = _email_message.get_header("to")[0]
        _receiver = models_developer.Profile.objects.get_or_create(
            str(uuid.uuid1(), ),
            email=_receiver_address[1],
            is_anonymous=True,
            nickname=_receiver_address[0],
        ).user

        _data["receiver"] = _receiver
        _data["receiver_address"] = _receiver_address[1]

        _receivers = list()
        _receiver_addresses = list()

        _receiver_addresses_raw = list()

        _receiver_addresses.extend(_email_message.get_header("bcc"), )
        _receiver_addresses.extend(_email_message.get_header("cc"), )

        _receiver_addresses_raw.extend(_email_message.get_header("bcc", ), )
        _receiver_addresses_raw.extend(_email_message.get_header("cc", ), )

        for i in _receiver_addresses :
            _receivers.append(
                models_developer.Profile.objects.get_or_create(
                    str(uuid.uuid1(), ),
                    email=i[1],
                    is_anonymous=True,
                    nickname=i[0],
                ).user,
            )

        _data["receivers_address"] = ", ".join(
            ("%s <%s>" % i for i in _receiver_addresses_raw if i), )

        _reply_to = _email_message.get_header("reply-to")
        _data["reply_to"] = _reply_to

        # parent & parent_top
        _parent = None

        # check whether this message is join message.
        _parsed = utils_common.parse_join_email(_data.get("receiver_address"), )
        if not _parsed :
            for (_none, i, ) in _receiver_addresses :
                _parsed = utils_common.parse_join_email(i, )
                if _parsed :
                    break

        if _parsed :
            _parent = utils_common.get_object_from_join_email(parsed=_parsed, )

        if not _parent :
            _references = list()
            _refs = _email_message.get_header("references")
            if _refs :
                _references.extend([i.strip() for i in _refs.split() if i.strip()], )

            _in_reply_to = _email_message.get_header("in-reply-to")
            if _in_reply_to :
                _data["parent_uid"] = utils_dialog.normalize_message_id(_in_reply_to, )
                _references.append(_in_reply_to, )

            if _references :
                _parent = None
                for i in range(len(_references) - 1, -1, -1, ) :
                    try :
                        _parent = models_dialog.Message.objects.get(
                            uid=utils_dialog.normalize_message_id(_references[i], ),
                        )
                    except ObjectDoesNotExist :
                        pass
                    else :
                        break

                _data["parent_uid"] = utils_dialog.normalize_message_id(_references[-1], )

        if _parent is None :
            _qs = models_dialog.Message.objects.filter(
                subject=re.compile("^fwd\: ", re.I).sub("", _data["subject"]),
            ).order_by("-time_sent")
            if _qs.count() > 0 :
                _parent = _qs[0].parent_top

        _data["parent"] = _parent

        # content & content_type
        _content = None
        for i in _email_message.get_payloads() :
            if not i.get("content_type").startswith("text/") :
                continue

            if i.get("content_type") == "text/html" :
                _content = i
                break

            _content = i

        if not _content :
            raise ValueError(u"No content payload.", )

        _data["content_type"] = _content.get("content_type")
        _payload = _content.get("payload")

        # handle cid
        _cids = list(_email_message.get_cids(decode=True, ))
        _cid_keys = [re.escape(i.get("cid")) for i in _cids]
        if _cid_keys and _content.get("content_type") == "text/html" :
            _r = re.compile(
                "['\"](cid|CID):(%s)['\"]" % "|".join(_cid_keys),
                re.M | re.U
            ).findall(_payload)

            _cids_dict = dict([(i.get("cid"), i, ) for i in _cids], )

            for (_none, _k, ) in _r :
                _payload = re.compile(
                    "['\"]cid:%s['\"]" % _k,
                    re.M | re.U
                ).sub(
                    u"data:%s;base64,%s" % (
                        _cids_dict.get(_k).get("mimetype"),
                        base64.b64encode(_cids_dict.get(_k).get("payload"), ),
                    ),
                    _payload,
                )

        _data["content"] = _payload

        _message = models_dialog.Message.objects.create(**_data)

        # handle attachments
        for i in _email_message.get_attachments() :
            if i.get("payload") is None :
                continue

            _f = StringIO.StringIO(i.get("payload"), )
            _file = InMemoryUploadedFile(
                _f,
                "payload",
                utils_dialog.normalize_filename(i.get("filename"), ),
                i.get("mimetype"),
                _f.len,
                None,
            )
            models_dialog.Payload.objects.create(
                message=_message,
                file=_file,
                filename=i.get("filename"),
                mimetype=i.get("mimetype"),
            )

        # add receivers
        if _receivers :
            _message.receivers = _receivers

        # findout the missing parent and children
        _qs = models_dialog.Message.objects.filter(
            parent_uid=_message.uid,
        )
        if _qs.count() > 0 :
            map(lambda x : x.update_parent(_message, ), _qs, )

        # ReferenceTag: connecting message with object.
        _objects = utils_dialog.parse_reference_tag(_message.content, )
        if _objects :
            for _r in _objects :
                if isinstance(_r, models_dialog.Message, ) :
                    if _message.parent_top == _r.parent_top :
                        pass
                    else :
                        _message.parent_top = _r.parent_top
                        _message.save()
                else :
                    models_dialog.ConnectedMessage.objects.get_or_create(
                        content_object=_r,
                        message=_message,
                    )

        # handle forwared message(as attachment,)
        for i in _email_message.get_forwarded_messages() :
            if i.get("payload") is None :
                continue

            for j in i.get("payload", list(), ) :
                (_message_forwarded, _result, ) = EmailHandler(j.as_string(), ).save()
                if _result and _message_forwarded.is_top :
                    _message_forwarded.update_parent(_message, )

        return (_message, True, )



