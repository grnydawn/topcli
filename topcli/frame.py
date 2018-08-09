# -*- coding: utf-8 -*-

"""Frame module."""

import os
import sys
import abc
import argparse

from .util import PY3, name_match

if PY3:

    import importlib
    __import__ = importlib.__import__

    from urllib.request import urlopen
    from urllib.parse import urlparse
    from urllib.error import HTTPError, URLError

else:

    from urllib2 import urlopen, HTTPError, URLError
    from urlparse import urlparse


class TaskFrame(object):

    __metaclass__ = abc.ABCMeta

    def __new__(cls, argv):

        parser = argparse.ArgumentParser()

#        parser.add_argument('--import-task', metavar='task', action='append', help='import task')
#        parser.add_argument('--import-function', metavar='function', action='append', help='import function')
#        parser.add_argument('--import-module', metavar='module', action='append', help='import module')
#        parser.add_argument('--name', metavar='task name', help='task name')
#        parser.add_argument('--calc', metavar='calc', action='append', help='python code for manipulating data.')
#        parser.add_argument('--output', metavar='output', action='append', help='output variable.')

        obj = super(TaskFrame, cls).__new__(cls)
        obj.parser = parser
        obj.targs = None

        return obj

    @abc.abstractmethod
    def __init__(self, argv):
        pass

    @classmethod
    def load_from_path(cls, path, fragment):
        mod = None
        if os.path.isfile(path):
            head, base = os.path.split(path)
            if base.endswith(".py"):
                sys.path.insert(0, head)
                mod = __import__(base[:-3])
                sys.path.pop(0)
        elif os.path.isdir(path):
            head, base = os.path.split(path)
            sys.path.insert(0, head)
            mod = __import__(base)
            sys.path.pop(0)

        candidates = {}
        if mod:
            for name in dir(mod):
                if not name.startswith("_"):
                    obj = getattr(mod, name)
                    if type(obj) == type(TaskFrame):
                        candidates[name] = obj

        if candidates:
            if fragment:
                return candidates.get(fragment, None)
            elif len(candidates) == 1:
                return candidates[0]
            else:
                import pdb; pdb.set_trace()

    @classmethod
    def load(cls, url, config):
        o = urlparse(url)
        if o.netloc:
            import pdb; pdb.set_trace()
        elif o.path:
            if os.path.exists(o.path):
                frame = cls.load_from_path(o.path, o.fragment)
                if frame: return frame

            if o.path in config.tasks:
                frame = config.tasks[o.path]
                if frame: return frame

            if o.path in config.taskconfig["names"]:
                if os.path.exists(config.taskconfig["names"][o.path]):
                    frame = cls.load_from_path(config.taskconfig["names"][o.path], o.fragment)
                    if frame: return frame
                else:
                    import pdb; pdb.set_trace()

            match = name_match(o.path, config.tasks.keys())
            if match:
                import pdb; pdb.set_trace()

            match = name_match(o.path, config.taskconfig["names"].keys())
            if match:
                import pdb; pdb.set_trace()

    def run(self, ctr, env):

        # add more options

        # parse options

        # ...

        # run perform
        self.perform(env)

    @abc.abstractmethod
    def perform(self, env):
        pass

class TaskFrameUnit(TaskFrame):
    pass

class TaskFrameGroup(TaskFrame):

    def __new__(cls, argv):

        obj = super(TaskFrameGroup, cls).__new__(cls, argv)
        obj.depends = {}

        return obj

    def add(self, instance, prev_instance):

        if instance not in self.depends:
            self.depends[instance] = []

        if prev_instance not in self.depends[instance]:
            self.depends[instance].append(prev_instance)

class SeqTaskFrameGroup(TaskFrameGroup):

    def __init__(self, argv):
        self.targs = self.parser.parse_args(argv)

    def perform(self, env):
        import pdb; pdb.set_trace()

def load_taskframe(taskname, config):

    if taskname in config.tasks:
        return config.tasks[taskname]
    else:
        import pdb; pdb.set_trace()

def build_taskgroup_from_argv(argv, config):

    # SeqTaskFrameGroup does not have its own argument
    taskgroup = SeqTaskFrameGroup([])

    targv = []
    prev_instance = None

    for arg in argv:
        if arg == "--":
            if targv:
                taskframe = load_taskframe(targv[0], config)
                taskinstance = taskframe(targv[1:])
                taskgroup.add(taskinstance, prev_instance)
                prev_instance = taskinstance
            targv = []
        else:
            targv.append(arg)

    if targv:
        taskframe = TaskFrame.load(targv[0], config)
        if taskframe:
            taskinstance = taskframe(targv[1:])
            taskgroup.add(taskinstance, prev_instance)
        else:
            import pdb; pdb.set_trace()

    return taskgroup
