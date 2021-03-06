#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `topcli` package."""

import os
import shlex
import shutil
import pytest

from topcli import main

here = os.path.dirname(__file__)
home = os.path.abspath(os.path.join(here, ".."))

def checktempfile(outfile):
    if outfile.isfile():
        out = outfile.size() > 0
        os.remove(str(outfile))
    elif outfile.isdir():
        out = outfile.join("0.pdf").size() > 0
        shutil.rmtree(str(outfile))
    else:
        out = False

    return out

def cmdnorm(cmd):
    return cmd.replace("\n", " ").replace("\\", "/")

@pytest.fixture(scope="session")
def outfile(tmpdir_factory):
    tempdir = tmpdir_factory.getbasetemp()
    outfile = tempdir.join('test.pdf')
    if outfile.isfile():
        os.remove(str(outfile))
    return outfile

def test_mpl(outfile):
    cmdline = """
        tasks/mpl.py
        "pd.read_csv('data/wetdepa.slope.csv', delimiter=';', header=None)"
        --calc "hwcs=D[0].iloc[:,2].drop_duplicates().values"
        --pages "len(hwcs)"
        --page-calc "HWC=D[0].loc[D[0].iloc[:,2]==hwcs[page_num],:]"
        -p "plot@HWC.iloc[:,3].values, HWC.iloc[:,4].values"
        -t "hwcs[page_num]"
        -x "label@'elapsed time(0: start, 1: end)'"
        -y  "label@'event'"
        --noshow
        --save "'%s'"
"""%str(outfile)

    """
   perform group fold
   -o "tnew@'-t', '--title', metavar='title', help='title  plotting.'"
   -r "2@'data=data'"
   -r "2@'-t#0=tnew'"
   --
   tasks/mpl.py
   --figure "text@0.25, 0.5,'Folding Report', fontsize=30"
   --axes "axis@'off'"
   --
   tasks/mpl.py
   "pd.read_csv('data/wetdepa.slope.csv', delimiter=';', header=None)"
   --calc "hwcs=D[0].iloc[:,2].drop_duplicates().values"
   --pages "len(hwcs)"
   --page-calc "HWC=D[0].loc[D[0].iloc[:,2]==hwcs[page_num],:]"
   -p "plot@HWC.iloc[:,3].values, HWC.iloc[:,4].values"
   -t "'ORIGINAL TITLE'"
   --
   tasks/mpl.py
   --figure "text@0.3, 0.5, 'Thank You', fontsize=30"
   --axes "axis@'off'"
"""
#   perform group fold -o "tnew@'-t', '--title', metavar='title', help='title  plotting.'" -r "2@'data=data'" -r "2@'-t#0=tnew'" -- tasks/mpl.py --figure "text@0.25, 0.5,'Folding Report', fontsize=30" --axes "axis@'off'" -- tasks/mpl.py "pd.read_csv('data/wetdepa.slope.csv', delimiter=';', header=None)" --calc "hwcs=D[0].iloc[:,2].drop_duplicates().values" --pages "len(hwcs)" --page-calc "HWC=D[0].loc[D[0].iloc[:,2]==hwcs[page_num],:]" -p "plot@HWC.iloc[:,3].values, HWC.iloc[:,4].values" -t "hwcs[page_num]" -- tasks/mpl.py --figure "text@0.3, 0.5, 'Q & A', fontsize=30" --axes "axis@'off'"
#   perform  fold "pd.read_csv('data/wetdepa.reduced.slope.csv', delimiter=';', header=None)" -t "'ttt'"


# NOTE: use promote to share object between tasks

    output = main(shlex.split(cmdnorm(cmdline)))
    assert checktempfile(outfile)
    assert output == 0

def test_print(outfile):
    cmdline = """
        tasks/print.py \
        "pd.read_csv('data/wetdepa.slope.csv', delimiter=';', header=None)" \
"""

    output = main(shlex.split(cmdnorm(cmdline)))
    assert output == 0
