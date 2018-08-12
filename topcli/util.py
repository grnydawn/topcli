# -*- coding: utf-8 -*-

"""utility module."""

import sys
import zipfile
import tempfile

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
        return list(k1) + k2

    def values(self):
        v1 = super(envdict, self).values()
        v2 = self.parent.values() if isinstance(self.parent, envdict) else []
        return list(v1) + v2

    def __iter__(self):
        for k in self.keys():
            yield k

    def items(self):
        for k in self.keys():
            yield k, self.__getitem__(k)

    iteritems = items

def is_taffile(path):

    # is zipfile
    if not zipfile.is_zipfile(path):
        return False

    taf = zipfile.ZipFile(path)

    try:
        tmeta = taf.getinfo("METAFILE")
        with taf.open("METAFILE") as mf:
            firstline = mf.readline().strip()
            return firstline == b"[MAGIC_TOPCLI]"
    except KeyError:
        return False

def extract_taffile(path):

    tmpdir = tempfile.mkdtemp()
    taf = zipfile.ZipFile(path)
    taf.extractall(path=tmpdir)

    return tmpdir

def get_dest(parser, arg):
    # _StoreAction, _AppendAction
    for act in parser._actions:
        if arg in act.option_strings or \
            (arg == "data" and act.dest == "data"):
            return act.dest
    return None

def get_nargs(parser, dest):
    for act in parser._actions:
        if act.dest == dest:
            return act.nargs

def get_action_name(parser, dest):
    for act in parser._actions:
        if act.dest == dest:
            return act.__class__.__name__
