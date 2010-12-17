# -*- coding: utf-8 -*-


"""

==================================================
Dialog
==================================================

Register message using Model
--------------------------------------------------

>>> _sender = models_auth.User.objects.all()[0]
>>> _sender_profile = models_developer.Profile.objects.get_by_user(_sender, )
>>> _receiver = models_auth.User.objects.all()[1]
>>> _receiver_profile = models_developer.Profile.objects.get_by_user(_receiver, )

>>> _m = dict(
...	    uid=str(uuid.uuid1(), ),
...	    sender=_sender,
...	    receiver=_receiver,
...	    subject=u"subject#1",
...	    content=u"content#1",
...	    content_type=u"text/plain",
...	    reply_to=u"%s" % _sender.email,
...	    time_sent=datetime.datetime.now() - datetime.timedelta(days=1, ), # yesterday
...	)
>>> _message = models_dialog.Message.objects.create(**_m)
>>> _message.receivers.add(_receiver, )

>>> _message.profilemessagetop_set.filter(profile=_sender_profile, )[0].labels.all()
[<Label: Inbox>]

Archive parent

>>> _message.profilemessagetop_set.filter(profile=_sender_profile, )[0].archive()
>>> _message.profilemessagetop_set.filter(profile=_sender_profile, )[0].labels.all()
[]

Verify model object

>>> _message.parent is None
True
>>> _message == _message.parent_top
True

>>> _m = dict(
...	    uid=str(uuid.uuid1(), ),
...	    sender=_receiver,
...	    receiver=_sender,
...	    subject=u"subject#1",
...	    content=u"content#1",
...	    content_type=u"text/plain",
...	    reply_to=u"%s" % _sender.email,
...	    parent=_message,
...	    time_sent=datetime.datetime.now() - datetime.timedelta(days=1, ), # yesterday
...	)
>>> _message_child = models_dialog.Message.objects.create(**_m)
>>> _message_child.receivers.add(_sender, )
>>> _message_child.parent_top == _message
True
>>> _message_child.parent_top == _message.parent_top
True

Get all children messages

>>> _message.all_children.all().order_by("time_added", )
[<Message: pk:1>, <Message: pk:2>]

Register message using API
--------------------------------------------------

If bad email format

>>> _response = CLIENT.post(URL_API, dict(message=u"thi si plain"), )
>>> _response.status_code # invaild email message
400

>>> _email_raw = file(os.path.dirname(__file__) + "/email_message0.txt").read()
>>> _email_message = _email.Message.from_string(_email_raw, )

>>> _response = CLIENT.post(URL_API, dict(message=_email_raw, ), )
>>> _response.status_code == 200
True

Verify in models

>>> _message = models_dialog.ProfileMessageTop.objects.get(
...     profile=_sender_profile,
...     message__uid=_email_message.get_header("message-id"), )
>>> _message0 = models_dialog.ProfileMessageTop.objects.all().order_by("-pk")[0]
>>> _message.message.uid == _message0.message.uid
True

>>> _message.archive()
>>> _message.labels.all()
[]
>>> _message.is_top
True

Register reply

>>> _email_raw = file(os.path.dirname(__file__) + "/email_message-reply_to0.txt").read()
>>> _email_message = _email.Message.from_string(_email_raw, )

>>> _response = CLIENT.post(URL_API, dict(message=_email_raw, ), )
>>> _response.status_code == 200
True

>>> _message = models_dialog.Message.objects.get(
...     uid=_email_message.get_header("message-id"), )
>>> _message_top = models_dialog.ProfileMessageTop.objects.get(
...     profile=_sender_profile,
...     message=_message.parent_top, )
>>> _message_top.labels.all()
[<Label: Inbox>]

Set label
--------------------------------------------------

>>> _reply = models_dialog.Message.objects.get(uid=_email_message.get_header("message-id"))
>>> _user_label = models_dialog.ProfileMessageTop.objects.get(
...     profile=_sender_profile, message=_reply.parent_top, )
>>> _user_label.labels.add(models_dialog.Label.objects.get_or_create(name=u"test", )[0])
>>> _user_label.labels.all()
[<Label: Inbox>, <Label: test>]
>>> _user_label.parent_top.labels.all()
[<Label: Inbox>, <Label: test>]

>>> (_pm, _created, ) = models_dialog.ProfileMessage.objects.get_or_create(
...     profile=_sender_profile,
...     message=_reply,
... )
>>> _pm.labels.add(models_dialog.Label.objects.get_or_create(name=u"new test", )[0], )
>>> _user_label.labels.all()
[<Label: Inbox>, <Label: new test>]

Filter top messages by label
--------------------------------------------------

>>> _qs = models_dialog.ProfileMessageTop.objects.filter(
...	    profile=_sender_profile,
...	    labels__name__in=[u"new test", ],
...	)
>>> _qs.count() == 1
True
>>> _qs[0].message == _reply.parent_top
True

Set star and read

>>> _pm.parent_top.is_read
False

>>> _pm.is_starred = True
>>> _pm.save()
>>> _pm.parent_top.is_starred == _pm.is_starred
True


Errors
==================================================

>>> _email_raw = file(os.path.dirname(__file__) + "/email_message-receivers.txt").read()
>>> _email_message = _email.Message.from_string(_email_raw, )

>>> _response = CLIENT.post(URL_API, dict(message=_email_raw, ), )
>>> _response.status_code == 200
True

>>> _message0 = models_dialog.Message.objects.get(uid=_email_message.get_header("message-id"))
>>> _user_message0 = models_dialog.ProfileMessageTop.objects.get(
...    profile=_sender_profile,
...    message__receiver=_sender,
...    message__uid=_email_message.get_header("message-id"),
... )
>>> _message0 == _user_message0.message
True

`Reference`(`In-Reply-To`) Test
==================================================

>>> False not in map(register, TEST_EMLS, )
True

>>> map(lambda x : x.uid, models_dialog.Message.objects.get(uid=u"mid-a", ).dialog, )
[u'mid-a', u'mid-a0', u'mid-a1', u'mid-a2']
>>> map(lambda x : x.uid, models_dialog.Message.objects.get(uid=u"mid-a0", ).dialog, )
[u'mid-a', u'mid-a0', u'mid-a1', u'mid-a2']
>>> map(lambda x : x.uid, models_dialog.Message.objects.get(uid=u"mid-a1", ).dialog, )
[u'mid-a', u'mid-a0', u'mid-a1', u'mid-a2']
>>> map(lambda x : x.uid, models_dialog.Message.objects.get(uid=u"mid-a2", ).dialog, )
[u'mid-a', u'mid-a0', u'mid-a1', u'mid-a2']

Delete all messages for simplicity

>>> models_dialog.Message.objects.all().delete()
>>> models_dialog.ProfileMessageTop.objects.all()
[]
>>> models_dialog.ProfileMessage.objects.all()
[]

Shuffle the order to register

>>> def shuffle_register () :
...    _new_emls = TEST_EMLS[:]
...    random.shuffle(_new_emls, )
...    if _new_emls == TEST_EMLS :
...        return None
... 
...    models_dialog.Message.objects.all().delete()
...    return False not in map(register, _new_emls, )

>>> False not in map(lambda x : shuffle_register(), range(3, ), )
True

Not UTF-8 message Handling
==================================================

>>> register("euc-kr.eml")
True

>>> _euc_kr_message = models_dialog.Message.objects.get(uid="<this_is_euc_kr_message>")
>>> _euc_kr_message.content
u"\uc870\ub9cc\uac04 \uc6b0\ub9ac\ub9cc\uc758 \uacf5\uac04\uc774 \ub9c8\ub828\ub418\uc11c '\uc18c\ud1b5\uc744 \ucd09\uc9c4\ud558\ub294 \uc120\ubb3c \ud68c\uc0ac' \ube68\ub9ac \ub9cc\ub4e4\uace0 \uc2f6\uc2b5\ub2c8\ub2e4."

Attachment Handling
==================================================

>>> _email_raw = file(os.path.dirname(__file__) + "/attachment.eml").read()
>>> _attch = _email.Message.from_string(_email_raw, )
>>> _atts = list(_attch.get_attachments())
>>> _atts[0].get("filename")
u'SHOW 2010\ub144 11\uc6d4 email \uba85\uc138\uc11c.html'
>>> _atts[0].get("mimetype")
'application/octet-stream'

Register attachment email
>>> register("attachment.eml")
True

>>> _attachment_message = models_dialog.Message.objects.get(uid="<4cdfd696.29edd80a.6e33.ffffd407SMTPIN_ADDED@mx.google.com>")
>>> _attachment_message.payloads.all().count() > 0
True
>>> _attachment_message.payloads.all()[0].filename
u'SHOW 2010\ub144 11\uc6d4 email \uba85\uc138\uc11c.html'
>>> _attachment_message.payloads.all()[0].mimetype
u'application/octet-stream'
>>> _attachment_message.payloads.all()[0].file.size
58608

Cid(Content-ID) Hanlding
==================================================

>>> _email_raw = file(os.path.dirname(__file__) + "/cid.eml").read()
>>> _cid_message = _email.Message.from_string(_email_raw, )
>>> _cids = list(_cid_message.get_cids())
>>> _cids[0].get("cid")
'ii_12ca5abaafef221b'
>>> _cids[0].get("mimetype")
'image/png'
>>> _cids[0].get("filename")
'S.Rothan.png'

Register cid email
>>> register("cid.eml")
True

>>> _cid_message_obj = models_dialog.Message.objects.get(uid="<AANLkTikCU-WJPanN746GFL=oYyUVHpCFvyM=ZSPqM7jU@mail.gmail.com>")
>>> [i[:40] for i in _cid_message_obj.content.split("<img src=")]
[u'', u'data:image/png;base64,iVBORw0KGgoAAAANSU', u'data:image/png;base64,iVBORw0KGgoAAAANSU']


Using Join-Email address
--------------------------------------------------

>>> _address = _cid_message_obj.join_email
>>> _email_raw = file(os.path.dirname(__file__) + "/mid-join_email.eml", ).read() % _address
>>> _response = CLIENT.post(URL_API, dict(message=_email_raw, ), )
>>> _response.status_code == 200
True

Check the parent relation

>>> _message = models_dialog.Message.objects.get(uid="mid-join-email", )
>>> _message.parent_top == _cid_message_obj
True

Reference Tag
==================================================

>>> (_project, _created, ) = models_project.Item.objects.get_or_create(
...     name="test0",
...     code="test0",
...     author=models_developer.Profile.objects.all()[0].user,
... )

>>> (_project, _created, ) = models_project.Item.objects.get_or_create(
...     name="test1",
...     code="test1",
...     author=models_developer.Profile.objects.all()[0].user,
... )

>>> _info_name = u"test1"
>>> _repository_url = prepare_svn(_project.code, _info_name, )

>>> (_info, _created, ) = models_version_control.Info.objects.get_or_create(
...     name=_info_name,
...     project=_project,
...     repository_url=_repository_url,
... )

>>> client = client_django()

>>> _url_api_revision = reverse("version_control_api_revision",
...    kwargs=dict(
...         project=_project.code,
...         name=_info.name,
...    ),
... )
>>> _response = client.post(_url_api_revision, )

>>> _response.status_code == 200
True
>>> _response.content
'Updated: latest revision is 7'

Connecting model object and message
--------------------------------------------------

>>> _mids = list()
>>> for eml in TEST_EMLS :
...   _msg = _email.Message.from_string(
...         file(os.path.dirname(__file__) + ("/%s" % eml), ).read(), )
...   _mids.append(_msg.get_header("message-id"), )

>>> _messages = list(models_dialog.Message.objects.filter(uid__in=_mids, ))

>>> for i in _messages[:2] :
...     models_dialog.ConnectedMessage.objects.get_or_create(
...         content_object=_project, message=i, ) is None and None or None

>>> _qs = models_dialog.ConnectedMessage.objects.filter(
...     _project,
...     project=_project,
...     message__uid=_messages[0].uid,
... )
>>> _qs[0] == _messages[0]
True

>>> _qs = models_dialog.ConnectedMessage.objects.filter(
...     uid=_messages[0].uid,
... )
>>> _qs[0] == _messages[0]
True

>>> _connected_message_0 = models_dialog.ConnectedMessage.objects.get(
...     _project,
...     project=_project,
...     message__uid=_messages[0].uid,
... )
>>> _connected_message_0 == _messages[0]
True

>>> for i in _messages[2:4] :
...     models_dialog.ConnectedMessage.objects.get_or_create(
...         content_object=_info, message=i, ) is None and None or None

>>> _qs = models_dialog.ConnectedMessage.objects.filter(
...     _info,
...     info=_info,
...     message__uid=_messages[2].uid,
... )
>>> _qs[0] == _messages[2]
True

>>> _qs = models_dialog.ConnectedMessage.objects.get(
...     _info,
...     info=_info,
...     message__uid=_messages[2].uid,
... )
>>> _qs == _messages[2]
True

Parsing reference tag
--------------------------------------------------

>>> _messages[0].reference_tag is not None
True

>>> _parsed = utils_dialog.parse_reference_tag(_messages[0].reference_tag, )
>>> _parsed[0] == _messages[0]
True

>>> _revision = models_version_control.Revision.objects.filter(info=_info, ).order_by("-number")[0]
>>> _revision.reference_tag
u'project:test1;vc:test1;r:7'
>>> _parsed = utils_dialog.parse_reference_tag(_revision.reference_tag, )
>>> _parsed[0] == _revision
True

>>> _parsed = utils_dialog.parse_reference_tag(_revision.files.all()[0].reference_tag, )
>>> _parsed[0] == _revision.files.all()[0]
True

>>> _parsed = utils_dialog.parse_reference_tag(_revision.files.all()[0].file.reference_tag, )
>>> _parsed[0]== _revision.files.all()[0].file
True

Connect message, which has reference tag with object.

>>> (_connected_message, _created, ) = models_dialog.ConnectedMessage.objects.get_or_create(
...     content_object=_parsed[0], message=_messages[-1], )

>>> _message_1 = models_dialog.ConnectedMessage.objects.get(
...     _parsed[0], message=_messages[-1], )

>>> _connected_message.message == _message_1
True

Importing message, which has reference tag

>>> _email_raw = file(os.path.dirname(__file__) + "/email-reference_tag.eml", ).read() % _revision.reference_tag
>>> (_message, _created, ) = forms_dialog.get_model("email", )(
...    _email_raw.encode("utf-8"), ).save()

Check it.

>>> _message_2 = models_dialog.ConnectedMessage.objects.get(
...     _revision, message=_message, )
>>> _message_2 == _message
True

Forwarded Message will be saved as normal message
==================================================

>>> register("email-forward-child.eml")
True
>>> _message = models_dialog.Message.objects.get(uid="<964260CA-DFBB-4D78-B3E3-8FD77D8DC721@cloudgifts.com>", )
>>> _fm = models_dialog.Message.objects.get(uid="<6712535985464653587@unknownmsgid>", )
>>> _fm.parent_top == _message.parent_top
True


"""

import os, uuid, datetime, random

from django.conf import settings
settings.DEBUG = True
from django.test.client import Client as client_django
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import Q
from django.contrib.auth import models as models_auth

from spikeekips import _email

from IO.dialog import models as models_dialog, forms as forms_dialog, utils as utils_dialog
from IO.project import models as models_project
from IO.version_control import models as models_version_control
from IO.developer import models as models_developer

from IO.version_control.tests import prepare_svn


TEST_EMLS = [
    "mid-a.eml",
    "mid-a0.eml",
    "mid-a1.eml",
    "mid-a2.eml",
]

CLIENT = client_django()
URL_API = reverse("dialog_api_message", kwargs=dict(message_type="email"), )

def register (eml, ) :
   _email_raw = file(os.path.dirname(__file__) + ("/%s" % eml), ).read()
   return CLIENT.post(URL_API, dict(message=_email_raw, ), ).status_code == 200



if __name__ == "__main__" :
    import doctest
    doctest.testmod()






