# -*- coding: utf-8 -*-

import difflib

def diff_content (source, target, ) :
    for i in difflib.Differ().compare(source, target, ) :
        if i.startswith("?") :
            i = i.decode("utf-8")
    
        yield i
    


