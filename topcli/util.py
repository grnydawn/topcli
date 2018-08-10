# -*- coding: utf-8 -*-

"""utility module."""

import sys

PY3 = sys.version_info >= (3, 0)

def name_match(pat, names):
    match = []
    p = pat.split(".")
    for name in names:
        n = name.split(".")
        if len(p) > len(n):
            return []
        for a, b in zip(p, n[:len(p)]):
            if a != b:
                return []
        match.append(name)
    return match

class envdict(dict):

    def __init__(self, *vargs, **kwargs):
        self.parent = None
        super(envdict, self).__init__(*vargs, **kwargs)

    def __getitem__(self, key):
        if key in self:
            return super(envdict, self).__getitem__(key)
        elif isinstance(self.parent, envdict):
            return self.parent[key]
        else:
            raise KeyError(str(key))

#    def __contains__(self, key):
#        if super(envdict, self).__contains__(key):
#            return True
#        elif isinstance(self.parent, envdict):
#            return key in self.parent
#        return False

    def keys(self):
        k1 = super(envdict, self).keys()
        k2 = self.parent.keys() if isinstance(self.parent, envdict) else []
        return k1 + k2

    def values(self):
        v1 = super(envdict, self).values()
        v2 = self.parent.values() if isinstance(self.parent, envdict) else []
        return v1 + v2

    def __iter__(self):
        for k in self.keys():
            yield k

    def items(self):
        for k in self.keys():
            yield k, self.__getitem__(k)

    iteritems = items
