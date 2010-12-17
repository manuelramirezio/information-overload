# -*- coding: utf-8 -*-

import uuid

def uid (l=None, ) :
    return str(uuid.uuid1())[:l and l or None]





