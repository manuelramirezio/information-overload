# -*- coding: utf-8 -*-


"""
Version Control: Test0, blank svn repository
==================================================

Create new project and version control
>>> (_project, _created, ) = models_project.Item.objects.get_or_create(
...     name="test0",
...     code="test0",
...     author=models_developer.Profile.objects.all()[0].user,
... )
>>> _project.version_control.all()
[]

Prepare svn repository

>>> _info_name = u"test0"
>>> _repository_url = prepare_svn(_project.code, _info_name, )

>>> (_info, _created, ) = models_version_control.Info.objects.get_or_create(
...     name=_info_name,
...     project=_project,
...     repository_url=_repository_url,
... )

>>> _info.project == _project
True

Testing Model
--------------------------------------------------

Create File

>>> _abspath = "this/is/just/file.txt"
>>> (_file, _created, ) = models_version_control.File.objects.get_or_create_with_abspath(
...    info=_info,
...    abspath=_abspath,
...    filetype="regular",
... )

>>> _created == True
True
>>> _file.name == u"file.txt"
True
>>> _file.abspath == _abspath
True
>>> _file.parent == models_version_control.File.objects.get(
...    info=_info, abspath=os.path.dirname(_abspath),
... )
True
>>> _file.parent.filetype
u'directory'

In the View
--------------------------------------------------

>>> _url_api_revision = reverse("version_control_api_revision",
...    kwargs=dict(
...         project=_project.code,
...         name=_info.name,
...    ),
... )
>>> client = client_django()

>>> _response = client.post(_url_api_revision, )
>>> _response.status_code == 304
True

Check in the model,

>>> models_version_control.Revision.objects.filter(info=_info, ).count() < 1
True

Version Control: Test1, not blank svn repository
==================================================

Create new project
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

>>> _info.project == _project
True

Testing Model
--------------------------------------------------

In the View
--------------------------------------------------

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

Get the latest revision in the model,

>>> models_version_control.Revision.objects.filter(info=_info, ).order_by("-number")[0].number == 7
True

Getting Diff in revision file

>>> _r1 = models_version_control.Revision.objects.get(number=1, )
>>> _diff1 = _r1.diff_by_number(0, )
>>> [i.abspath for i in _diff1]
[u'd1/f1.txt', u'd1/f2.txt']

>>> _r2 = models_version_control.Revision.objects.get(number=7, )
>>> _diff2 = _r2.diff_by_number(2, )
>>> [i.abspath for i in _diff2]
[u'd1/f1.txt', u'd1/revision4.txt', u'default.png']

>>> _r4 = models_version_control.Revision.objects.get(number=4, )
>>> _rf4 = _r4.files.get(file__abspath="d1/f1.txt", )
>>> for i in _rf4.diff_by_number(1, ).get("diff"): print [i, ]
['  Eni sed mus ut. Nibh blandit duis, mi pellentesque tempus neque odio.']
['  ']
['- Curae est morbi ligula lacus dui vivamus ut, nisi duis vitae habitas']
[u'?                                                        ^ ^^\n']
['+ Curae est morbi ligula lacus dui vivamus ut, nisi duis modified line habitas']
[u'?                                                        ^^^ ^^^^^^^^\n']
['+ added row']




"""

import os, pysvn, difflib, shutil, logging
#logging.basicConfig(level=logging.DEBUG, )

from pprint import pprint

from django.conf import settings
settings.DEBUG = True
from django.test.client import Client as client_django
from django.core.urlresolvers import reverse

from IO.developer import models as models_developer
from IO.project import models as models_project
from IO.common import models as models_common
from IO.version_control import models as models_version_control

def prepare_svn (code, name, ) :
    _svnroot = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "%s-svnroot" % name,
        ),
    )
    _path = models_version_control.get_repository_path(code, name)
    remove_svn(code, name, )

    _client = pysvn.Client()
    _url = "file://%s" % _svnroot
    try :
        _client.checkout(_url, _path, )
    except pysvn.ClientError :
        return None

    return _url

def remove_svn (code, name, ) :
    _path = models_version_control.get_repository_path(code, name)
    if os.path.exists(_path) :
        shutil.rmtree(_path, )

    return

if __name__ == "__main__" :
    import doctest
    doctest.testmod()






