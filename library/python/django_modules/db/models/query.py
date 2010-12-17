# -*- coding: utf-8 -*-

from django.db.models import Q
from django.utils.copycompat import deepcopy

def translate_query (query, func=lambda x : x, ) :
    _query = deepcopy(query, )
    for i in range(len(_query.children, ), ) :
        _q = _query.children[i]
        if isinstance(_q, Q, ) :
            _q = translate_query(_q, func=func, )
        elif isinstance(_q, tuple, ) :
            _q = func(_q, )

        _query.children[i] = _q

    return _query


