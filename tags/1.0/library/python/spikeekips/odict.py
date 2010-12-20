# -*- coding: utf-8 -*-

import UserDict

class OrderedDict (UserDict.IterableUserDict, ) :
    def __init__ (self, *a, **kw) :
        UserDict.UserDict.__init__(self, )

        self._o = list()
        self.update(*a, **kw)

    def update (self, *a, **kw) :
        if a :
            for i in a :
                if hasattr(i, "__iter__") :
                    for k, v in i :
                        self[k] = v
                elif hasattr(i, "items") :
                    for k, v in i.items() :
                        self[k] = v

        if kw :
            for k, v in kw.items() :
                self[k] = v

    def __setitem__ (self, k, v, ) :
        """
        >>> _kl = range(10)
        >>> random.shuffle(_kl)
        >>> _normal_dict = dict((i, i, ) for i in _kl)
        >>> _normal_dict.keys()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        >>> OrderedDict((i, i, ) for i in _kl).keys() == _kl
        True
        """
        if k not in self._o :
            self._o.append(k, )

        return UserDict.UserDict.__setitem__(self, k, v, )

    def __delitem__ (self, k, ) :
        """
        >>> _kl = range(10)
        >>> random.shuffle(_kl)
        >>> _or = OrderedDict((i, i, ) for i in _kl)
        >>> _or.keys() == _kl
        True

        >>> _k = random.choice(_kl)
        >>> del _or[_k]
        >>> del _kl[_kl.index(_k)]
        >>> _or.keys() == _kl
        True
        """
        UserDict.UserDict.__delitem__(self, k, )
        del self._o[self._o.index(k)]

    def __iter__ (self, ) :
        """
        >>> _kl = range(10)
        >>> random.shuffle(_kl)
        >>> _or = OrderedDict((i, i, ) for i in _kl)
        >>> list(_or.__iter__()) == _kl
        True
        """

        for i in self._o :
            yield i

    def keys (self, ) :
        """
        >>> _kl = range(10)
        >>> random.shuffle(_kl)
        >>> _or = OrderedDict((i, i, ) for i in _kl)
        >>> _or.keys() == _kl
        True
        """

        return self._o

    def values (self, ) :
        """
        >>> _kl = range(10)
        >>> random.shuffle(_kl)
        >>> _or = OrderedDict((i, i, ) for i in _kl)
        >>> _or.values() == _kl
        True
        """

        return [self.get(k) for k in self._o]

    def itervalues (self, ) :
        for i in self._o :
            yield self.get(i)

    def items (self, ) :
        """
        >>> _kl = range(10)
        >>> random.shuffle(_kl)
        >>> _or = OrderedDict((i, i, ) for i in _kl)
        >>> _or.items() == [(i, i, ) for i in _kl]
        True
        """

        return [(k, self.get(k), ) for k in self._o]

    def iteritems (self, ) :
        """
        >>> _kl = range(10)
        >>> random.shuffle(_kl)
        >>> _or = OrderedDict((i, i, ) for i in _kl)
        >>> list(_or.iteritems()) == [(i, i, ) for i in _kl]
        True
        """

        for i in self._o :
            yield (i, self.get(i), )

    def get_next (self, k, ) :
        return self.get(self._o[self._o.index(k) + 1])

    def get_previous (self, k, ) :
        return self.get(self._o[self._o.index(k) - 1])

    def append_to (self, o, k, v, ) :
        self._o.insert(
            self._o.index(o) + 1,
            k,
        )
        return UserDict.UserDict.__setitem__(self, k, v, )

    def __getslice__ (self, i, j, ) :
        """
        >>> _kl = range(10)
        >>> _or = OrderedDict((i, i, ) for i in _kl)
        >>> _kl[1:4] == _or[1:4]
        True
        """
        if not (i and j) :
            return self.values()

        return [self.get(i) for i in self._o[i:j]]

    def __delslice__ (self, i, j, ) :
        for i in self._o[i:j] :
            del self[i]

    def index (self, k, ) :
        return self._o.index(k)


if __name__ == "__main__" :
    import doctest, random
    doctest.testmod()

