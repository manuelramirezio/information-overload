# -*- coding: utf-8 -*-

import re

from django.conf import settings
from django.db.models import get_model, ObjectDoesNotExist

def parse_join_email (address, check_model_exist=True, ) :
    """
    >>> (_app_label, _module_name, _oid, ) = ("common", "configuration", "this_is_oid", )
    >>> _e = "%s+%s-%s-%s@%s" % (settings.EMAIL_IO_SERVICE_PARTED[0], _app_label, _module_name, _oid, settings.EMAIL_IO_SERVICE_PARTED[1])

    >>> _p = parse_join_email(_e, )
    >>> _p.get("app_label") == _app_label
    True
    >>> _p.get("module_name") == _module_name
    True
    >>> _p.get("oid") == _oid
    True
    >>> _p.get("model")._meta.app_label == _app_label
    True
    """

    _parted = address.split("@", 1, )
    if _parted[1] != settings.EMAIL_IO_SERVICE_PARTED[1] :
        return None

    _base_parted = _parted[0].split("+", 1, )
    if _base_parted[0] != settings.EMAIL_IO_SERVICE_PARTED[0] :
        return None

    try :
        (_app_label, _module_name, _oid, ) = _base_parted[1].split("-")
    except :
        return None

    _model = get_model(_app_label, _module_name)
    if check_model_exist and not _model :
        return None

    return dict(
        model=_model,
        oid=_oid,
        app_label=_app_label,
        module_name=_module_name,
    )

def get_object_from_join_email (address=None, parsed=None, ) :
    if address and not parsed :
        parsed = parse_join_email(address, check_model_exist=True, )

    if not parsed :
        return None

    try :
        return parsed.get("model").objects.get(oid=parsed.get("oid"), )
    except ObjectDoesNotExist :
        return None

RE_REFERENCE_TAG = re.compile(
    "([\s\"\'\.;]|)(?P<key>[\w]+)\:(?P<value>[\w\_\-\.\/]*[\w\_\-\/])([\s\"\'\.;]|)",
    re.I | re.M
)

RE_REFERENCE_TAG_BLANK = re.compile("[\s,][\s,]*")

def parse_reference_tag (content, ) :
    """
    >>> _c = "dkfajsd a:tag dlkfjasdlk"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}]]
    >>> _c = "dkfjasl\\"a:tag\\"dlfja"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}]]

    >>> _c = "dklfjasl\\"a:tag\\",dfalks"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}]]

    >>> _c = "dlfja,a:tag,a::"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}]]

    >>> _c = "dlfja,a:tag,b:tag0"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}], [{'value': 'tag0', 'key': 'b'}]]

    >>> _c = "dlfja,a:tag,b:tag0:dirdir:"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}], [{'value': 'tag0', 'key': 'b'}]]

    >>> _c = ",a:tag,atag"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}]]

    >>> _c = ",a:tag;b:tag0"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}, {'value': 'tag0', 'key': 'b'}]]

    >>> _c = ",a:tag;b:/this/is/path/"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}, {'value': '/this/is/path/', 'key': 'b'}]]

    >>> _c = ",a:tag;b:this/is/path"
    >>> parse_reference_tag(_c, )
    [[{'value': 'tag', 'key': 'a'}, {'value': 'this/is/path', 'key': 'b'}]]

    >>> _c = ",a:t-ag;b:this/is/path"
    >>> parse_reference_tag(_c, )
    [[{'value': 't-ag', 'key': 'a'}, {'value': 'this/is/path', 'key': 'b'}]]

    >>> _c = ",a:t-ag;b:this/is/path."
    >>> parse_reference_tag(_c, )
    [[{'value': 't-ag', 'key': 'a'}, {'value': 'this/is/path', 'key': 'b'}]]

    >>> _c = ",a:t-ag;b:this/is/path;c:show-me."
    >>> parse_reference_tag(_c, )
    [[{'value': 't-ag', 'key': 'a'}, {'value': 'this/is/path', 'key': 'b'}, {'value': 'show-me', 'key': 'c'}]]

    >>> _c = 'project:test1;vc:test1;r:7'
    >>> parse_reference_tag(_c, )
    [[{'value': 'test1', 'key': 'project'}, {'value': 'test1', 'key': 'vc'}, {'value': '7', 'key': 'r'}]]

    >>> _c = '<img src="cid:ii_12ca5abaafef221b" alt="S.Rothan.png" title="S.Rothan.png"><br>\\nproject:test1;vc:test1;r:7\\n<img src="cid:ii_12ca5abaafef221b1" alt="S.Rothan.png" title="S.Rothan.png"><br>'
    >>> parse_reference_tag(_c, )



    """

    _o = list()
    for i in RE_REFERENCE_TAG_BLANK.split(content, ) :
        _l = list()
        for (_none, _key, _value, _none, ) in RE_REFERENCE_TAG.findall(i, ) :
            _l.append(dict(key=_key, value=_value, ), )

        if len(_l) < 1 :
            continue

        _o.append(_l, )

    return _o

if __name__ == "__main__" :
    import doctest
    doctest.testmod()





