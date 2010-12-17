# -*- coding: utf-8 -*-

import os, hashlib

from django.db.models import Max, manager, ObjectDoesNotExist, Q

from IO.common import utils as utils_common

def normalize_message_id (s, ) :
    if len(s) < 255 :
        return s

    if type(s) in (unicode, ) :
        s = s.encode("utf-8")

    return u"sha1:%s" % hashlib.sha1(s).hexdigest()

def normalize_filename (s, ) :
    if type(s) in (unicode, ) :
        s = s.encode("utf-8")

    (_fname, _ext, ) = os.path.splitext(s, )

    return u"sha1-%s%s" % (hashlib.sha1(s).hexdigest(), _ext, )

class BaseReferenceTagParser (object, ) :
    @classmethod
    def parse (cls, s, ) :
        return cls(s, )._parse()

    def __init__ (self, p, ) :
        self._p = p

    def _parse (self, ) :
        raise NotImplemented


class ReferenceTagParser_dialog (BaseReferenceTagParser, ) :
    def _parse (self, ) :
        if self._p[0].get("key") != "dialog" :
            return None

        from IO.dialog import models as models_dialog
        try :
            return models_dialog.Message.objects.get(oid=self._p[0].get("value"), )
        except ObjectDoesNotExist :
            pass

        return None

class ReferenceTagParser_project (BaseReferenceTagParser, ) :
    def __init__ (self, *a, **kw) :
        super(ReferenceTagParser_project, self).__init__(*a, **kw)
        self._project = None
        self._info = None
        self._revision = None
        self._revision_file = None
        self._file = None

    def _parse (self, ) :
        if self._p[0].get("key") != "project" :
            return None

        from IO.project import models as models_project
        try :
            self._project = models_project.Item.objects.get(code=self._p[0].get("value"), )
        except ObjectDoesNotExist :
            return None

        _object = None
        for i in self._p[1:] :
            _m = "_parse_%s" % i.get("key", "").lower()
            if not hasattr(self, _m, ) :
                return None

            _object = getattr(self, _m, )(i, )
            if _object is None :
                return None

        return _object

    def _parse_vc (self, v, ) :
        from IO.version_control import models as models_version_control
        try :
            self._info = models_version_control.Info.objects.get(name=v.get("value"), )
        except ObjectDoesNotExist :
            return None

        return self._info

    def _parse_r (self, v, ) :
        from IO.version_control import models as models_version_control
        try :
            self._revision = self._info.revision.get(number=int(v.get("value"), ), )
        except (ObjectDoesNotExist, TypeError, ValueError, ) :
            return None

        return self._revision

    def _parse_f (self, v, ) :
        from IO.version_control import models as models_version_control

        _object = _file = None
        _path = models_version_control.File.normalize_path(v.get("value", "").strip(), )
        for _filetype in (
                    models_version_control.FILE_FIELD_TYPE_REGULAR,
                    models_version_control.FILE_FIELD_TYPE_DIRECTORY,
                ) :
            try :
                _file = self._info.files.get(
                    uid=models_version_control.File.get_uid(_path, _filetype, ),
                )
                break
            except ObjectDoesNotExist :
                pass

        if not _file :
            return None

        if not self._revision :
            return _file

        if _file.filetype == models_version_control.FILE_FIELD_TYPE_DIRECTORY :
            return self._revision

        try :
            return self._revision.files.get(file=_file, )
        except ObjectDoesNotExist :
            pass

def parse_reference_tag (content, ) :
    _o = utils_common.parse_reference_tag(content, )
    if not _o :
        return None

    _objects = list()
    for i in _o :
        _m = globals().get("ReferenceTagParser_%s" % i[0].get("key", "").lower(), )
        if not _m :
            continue

        _p = _m.parse(i, )
        if _p is None :
            continue

        _objects.append(_p, )

    return list(set(_objects, ), )


