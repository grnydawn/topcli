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
