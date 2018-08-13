# -*- coding: utf-8 -*-

"""builtin task module."""


import os
import shutil
import tempfile
import zipfile

from .util import PY3, name_match
from .frame import TaskFrame, TaskFrameUnit

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
            self.error_exit("'group' task requires only one positional argument.")

        self.group_name = self.targs.data.pop(0)
        self.data_args = self.targs.data
        self.targs.data = []

    def perform(self):

        def _u(text):
            _u.cnt += 1
            return "%s.%d"%(text, _u.cnt)
        _u.cnt = 0

        # check if ...
        if not isinstance(self.parent, TaskFrame) or \
            len(self.parent.subframes) < 2:
            self.error_exit("No task to group was found.")

        meta = configparser.ConfigParser()

        tmpdir = tempfile.mkdtemp()

        meta.add_section('MAGIC_TOPCLI')

        meta.add_section('OPTION')
        if self.targs.option:
            for option_arg in self.targs.option:
                split = [s.strip() for s in option_arg.split("@")]
                items = split[:-1]
                if len(items) == 1:
                    meta.set('OPTION', _u(items[0]), split[-1])
                else:
                    self.error_exit("Wrong syntax near '%s'."%option_arg)

        meta.add_section('REPLACE')
        if self.targs.replace:
            for replace_arg in self.targs.replace:
                split = [s.strip() for s in replace_arg.split("@")]
                #vargs, kwargs = self.parse_args(split[-1])
                items = split[:-1]
                if len(items) == 0:
                    #meta.set('REPLACE', "'*'", str((vargs, kwargs)))
                    meta.set('REPLACE', _u('*'), split[-1])
                elif len(items) == 1:
                    #meta.set('REPLACE', "'%s'"%items[0], str((vargs, kwargs)))
                    meta.set('REPLACE', _u(items[0]), split[-1])
                else:
                    self.error_exit("Wrong syntax near '%s'."%replace_arg)

        meta.add_section('APPEND')
        if self.targs.append:
            for append_arg in self.targs.append:
                split = [s.strip() for s in append_arg.split("@")]
                #items, vargs, kwargs = self.teval_atargs(append_arg)
                items = split[:-1]
                if len(items) == 0:
                    meta.set('APPEND', _u('*'), split[-1])
                elif len(items) == 1:
                    meta.set('APPEND', _u(items[0]), split[-1])
                else:
                    self.error_exit("Wrong syntax near '%s'."%append_arg)

        meta.add_section('DELETE')
        if self.targs.delete:
            for delete_arg in self.targs.delete:
                split = [s.strip() for s in delete_arg.split("@")]
                #items, vargs, kwargs = self.teval_atargs(delete_arg)
                items = split[:-1]
                if len(items) == 0:
                    #meta.set('DELETE', "'*'", str((vargs, kwargs)))
                    meta.set('DELETE', _u('*'), split[-1])
                elif len(items) == 1:
                    meta.set('DELETE', _u(items[0]), split[-1])
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
                meta.set('TASK', str(idx), str([frame.turl] + frame.targv))

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
            taf = self.group_name

        with zipfile.ZipFile(taf, 'w', allowZip64=True) as zf:
            addToZip(zf, tmpdir, '')

        shutil.rmtree(tmpdir)

        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

class InstallTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        # copy task definition into topcli home directory and set name mapping

        self.targs = self.parser.parse_args(argv)

        if len(self.targs.data) != 2:
            self.error_exit("'install' task requires two positional arguments.")

        self.task_name = self.targs.data.pop(0)
        self.task_namepath = [s.strip() for s in self.task_name.split(".")]
        self.task_loc = self.targs.data.pop(0)

        if len(self.task_namepath) != 3:
            self.error_exit("""
Task name should have a form of 'name3.name2.name1', but '%s' has two subnames only.
You may only use 'name3' or 'name3.name2' to launch this task if not confused."""%self.task_name)

        if self.task_namepath[0] in builtin_taskframes:
            self.error_exit("""
Task subname, '%s' is already used as a builtin task name.
%s are current builtin task names.
Please choose a task subname other than above builitin task names."""%(self.task_namepath[0], builtin_taskframes.keys()))

    def perform(self):

        task_instance = TaskFrame.load(self.task_loc, [], self.ctr, self, self.env)

        if task_instance:

            root, base = os.path.split(task_instance.turl)

            taskdir = self.ctr.config.paths['taskdir']
            taskconfig = self.ctr.config.taskconfig
            taskname = self.task_name.replace(".", "_")
            dst = os.path.join(taskdir, "%s_%s"%(taskname, base))

            if os.path.exists(dst):
                self.error_exit("'%s' already exists."%self.task_name)

            if os.path.isfile(task_instance.turl):
                shutil.copyfile(task_instance.turl, dst)
            elif os.path.isdir(task_instance.turl):
                shutil.copy(task_instance.turl, dst)

            taskconfig["names"][self.task_name] = dst

        # if passed, copy and revise METAFILE
        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

class UninstallTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        # copy task definition into topcli home directory and set name mapping

        self.targs = self.parser.parse_args(argv)

        if len(self.targs.data) != 1:
            self.error_exit("'uninstall' task requires only one positional arguments.")

        self.task_name = self.targs.data.pop(0)
        self.task_namepath = [s.strip() for s in self.task_name.split(".")]

        if self.task_name in builtin_taskframes:
            self.error_exit("Builtin task, '%s' can not be uninstalled."%self.task_name)

    def perform(self):

        frame_names = name_match(self.task_name, self.ctr.config.taskconfig["names"])

        if len(frame_names) == 1:
            frame_name = frame_names[0]
            frame = self.ctr.config.taskconfig["names"][frame_name]
            if not os.path.exists(frame):
                TaskFrame.error_exit("Task named '%s' is not found."%self.task_name)
            if os.path.isfile(frame):
                os.remove(frame)
            elif os.path.isdir(frame):
                shutil.rmtree(frame)
            del self.ctr.config.taskconfig["names"][frame_name]
        elif len(frame_names) > 1:
            TaskFrame.error_exit("Given task name, '%s', matches multiple tasks: %s"%(self.task_name, str(frame_names)))
        elif len(frame_names) == 0:
            TaskFrame.error_exit("Given task name, '%s', does not match any installed tasks"%self.task_name)

        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

class AliasTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        #perform alias fold --macro "ss@D[0]"
        self.parser.add_argument('-m', '--macro', action='append', help='macro definition.')

        self.targs = self.parser.parse_args(argv)

        if len(self.targs.data) == 1:
            self.alias_name = self.targs.data.pop(0)

            if self.alias_name in self.ctr.config.taskconfig["aliases"]:
                # TODO check if it matches with builtin and installed task name
                self.error_exit("Alias name, '%s', already exists."%self.alias_name)

        elif len(self.targs.data) > 1:
            self.error_exit("'group' task requires only one positional argument.")
        else:
            self.alias_name = None
            print("aliased task(s): %s"%", ".join(self.ctr.config.taskconfig["aliases"].keys()))

        # TODO: builtin name, installed task

    def perform(self):

        cmds = []

        if hasattr(self.parent, "depends"):
            frame = self.parent.depends[self]
            while frame:
                tcmds = []
                tcmds.append(frame.turl)
                tcmds.extend(frame.targv)
                cmds.append(tcmds)
                frame = self.parent.depends[frame]

        if self.alias_name:
            self.ctr.config.taskconfig["aliases"][self.alias_name] = [self.targs.macro, cmds]

        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

class UnaliasTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        self.targs = self.parser.parse_args(argv)

        if len(self.targs.data) == 0:
            self.error_exit("'unalias' task requires at least one positional arguments.")

        self.alias_names = self.targs.data
        self.targs.data = []

        for alias_name in self.alias_names:
            # TODO: check valid name syntax
            if alias_name not in self.ctr.config.taskconfig["aliases"]:
                self.error_exit("No alias name of '%s' is found.."%alias_name)

    def perform(self):

        for alias_name in self.alias_names:
            del self.ctr.config.taskconfig["aliases"][alias_name]

        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

class HistoryTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        self.targs = self.parser.parse_args(argv)

    def perform(self):

        for idx, hist in enumerate(self.ctr.config.histconfig["list"]):
            print(" %d  %s"%(idx, " ".join(hist)))

        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

class ListTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        self.targs = self.parser.parse_args(argv)

    def perform(self):

        print("Installed tasks: %s"%" ".join(self.ctr.config.taskconfig["names"].keys()))
        print("Aliased   tasks: %s"%" ".join(self.ctr.config.taskconfig["aliases"].keys()))

        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

class HelpTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, url, argv, env):

        self.targs = self.parser.parse_args(argv)

        if len(self.targs.data) < 1:
            self.error_exit("'help' task requires at least one positional arguments.")

        self.target_names = self.targs.data
        self.targs.data = []

    def perform(self):

        print("Under development.")

        if hasattr(self.parent, "depends"):
            self.parent.depends[self] = None

builtin_taskframes = {
    "group":        GroupTaskFrame,
    "install":      InstallTaskFrame,
    "uninstall":    UninstallTaskFrame,
    "alias":        AliasTaskFrame,
    "unalias":      UnaliasTaskFrame,
    "history":      HistoryTaskFrame,
    "list":         ListTaskFrame,
    "help":         HelpTaskFrame,
}
