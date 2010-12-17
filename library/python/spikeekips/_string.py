# -*- coding: utf-8 -*-


def to_utf8 (s, encoding="utf-8", ) :
    if type(s) in (unicode, ) :
        s = s.encode("utf-8")
    elif encoding != "utf-8" :
        s = s.decode(encoding, ).encode("utf-8")

    return s




