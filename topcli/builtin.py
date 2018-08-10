# -*- coding: utf-8 -*-

"""builtin task module."""


import os
import shutil
import tempfile
import zipfile

from .util import PY3
from .frame import TaskFrameUnit

if PY3:
    import configparser
else:
    import ConfigParser as configparser


class GroupTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        # map grouptask option to subtask option

        # name@argparse options
        self.parser.add_argument('-o', '--option', action='append', help='option definition.')

        self.parser.add_argument('-r', '--replace', action='append', help='option fowarding.')
        self.parser.add_argument('-a', '--append', action='append', help='option addition.')
        self.parser.add_argument('-d', '--delete', action='append', help='option deletion.')

        self.parser.add_argument('--output', help='output path.')

        self.targs = self.parser.parse_args(argv)

        if len(self.targs.data) != 1:
            self.error_exit("'group' task requires one positional argument.")

        self.group_name = self.targs.data.pop()

    def perform(self):

        meta = configparser.ConfigParser()

        tmpdir = tempfile.mkdtemp()

        meta.add_section('MAGIC_TOPCLI')

        meta.add_section('OPTION')
        if self.targs.option:
            for option_arg in self.targs.option:
                items, vargs, kwargs = self.teval_atargs(option_arg)
                if len(items) == 1:
                    meta.set('OPTION', items[0], (vargs, kwargs))
                else:
                    self.error_exit("Wrong syntax near '%s'."%option_arg)

        meta.add_section('REPLACE')
        if self.targs.replace:
            for replace_org in self.targs.replace:
                items, vargs, kwargs = self.teval_atargs(replace_arg)
                if len(items) == 1:
                    meta.set('REPLACE', ["'*'", items[0]], (vargs, kwargs))
                elif len(items) == 2:
                    meta.set('REPLACE', items, (vargs, kwargs))
                else:
                    self.error_exit("Wrong syntax near '%s'."%replace_arg)

        meta.add_section('APPEND')
        if self.targs.append:
            for append_arg in self.targs.append:
                items, vargs, kwargs = self.teval_atargs(append_arg)
                if len(items) == 0:
                    meta.set('APPEND', "'*'", (vargs, kwargs))
                elif len(items) == 1:
                    meta.set('APPEND', items[0], (vargs, kwargs))
                else:
                    self.error_exit("Wrong syntax near '%s'."%append_arg)

        meta.add_section('DELETE')
        if self.targs.delete:
            for delete_arg in self.targs.delete:
                items, vargs, kwargs = self.teval_atargs(delete_arg)
                if len(items) == 0:
                    meta.set('DELETE', "'*'", (vargs, kwargs))
                elif len(items) == 1:
                    meta.set('DELETE', items[0], (vargs, kwargs))
                else:
                    self.error_exit("Wrong syntax near '%s'."%delete_arg)

        # TODO: put additional data into tmpdir

        meta.add_section('TASK')

        frame = self
        idx = 0
        while frame:
            idx += 1
            frame = self.parent.depends[frame]
            if frame:
                meta.set('TASK', str(idx), [frame.turl] + frame.targv)

        with open(os.path.join(tmpdir, "METAFILE"), "w") as mf:
            meta.write(mf)

        def addToZip(zf, path, zippath):
            if os.path.isfile(path):
                zf.write(path, zippath, zipfile.ZIP_DEFLATED)
            elif os.path.isdir(path):
                if zippath:
                    zf.write(path, zippath)
                for nm in os.listdir(path):
                    addToZip(zf, os.path.join(path, nm), os.path.join(zippath, nm))

        taf = self.targs.output
        if taf is None:
            taf = "%s.taf"%self.group_name

        with zipfile.ZipFile(taf, 'w', allowZip64=True) as zf:
            addToZip(zf, tmpdir, '')

        shutil.rmtree(tmpdir)

builtin_taskframes = {
    "group":      GroupTaskFrame,
}
