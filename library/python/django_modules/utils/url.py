# -*- coding: utf-8 -*-

def get_path (request, ) :
    _qs = request.META.get("QUERY_STRING", "")
    return "%s%s" % (
        request.META.get("PATH_INFO"),
        _qs and ("?%s" % _qs) or "",
    )


