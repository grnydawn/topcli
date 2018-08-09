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

    def __new__(cls, argv, env):

        parser = argparse.ArgumentParser()

        parser.add_argument('data', metavar='<input data>', nargs="*", help='input data')

#        parser.add_argument('--import-task', metavar='task', action='append', help='import task')
#        parser.add_argument('--import-function', metavar='function', action='append', help='import function')
#        parser.add_argument('--import-module', metavar='module', action='append', help='import module')
#        parser.add_argument('--name', metavar='task name', help='task name')
        parser.add_argument('--calc', metavar='calc', action='append', help='python code for manipulating data.')
#        parser.add_argument('--output', metavar='output', action='append', help='output variable.')

        obj = super(TaskFrame, cls).__new__(cls)
        obj.parser = parser
        obj.env = env
        obj.targs = None

        return obj

    @abc.abstractmethod
    def __init__(self, argv, env):
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
                return candidates.values()[0]
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

    def run(self, ctr):

        self.ctr = ctr

        # parse common options

        # data
        data = []
        for d in self.targs.data:
            obj = self.teval(d)
            data.append(obj)
        self.env["D"] = data

        if self.targs.calc:
            for calc in self.targs.calc:
                vargs, kwargs = self.teval_args(calc)
                self.env.update(kwargs)


        # ...

        # run perform
        self.perform()

    @abc.abstractmethod
    def perform(self):
        pass

    def error_exit(self, msg):
        # TODO: coordinate with self.ctr

        print("ERROR: "+msg)
        sys.exit(-1)

    def teval(self, expr, **kwargs):
        try:
            return eval(expr, self.env, kwargs)
        except NameError as err:
            self.error_exit('EVAL: '+str(err))
        except TypeError as err:
            import pdb; pdb.set_trace()

    def teval_args(self, args, **kwargs):

        def _p(*args, **kw_str):
            return list(args), kw_str

        return self.teval('_p(%s)'%args, _p=_p, **kwargs)

    def teval_atargs(self, expr, **kwargs):
        s = [i.strip() for i in expr.split("@")]
        v, k = self.teval_args(s[-1], **kwargs)
        return s[:-1], v, k

    def teval_func(self, func, *vargs, **kwargs):

        return self.teval('_f_(*_v_, **_k_)', _f_=func,
            _v_=vargs, _k_=kwargs)

class TaskFrameUnit(TaskFrame):
    pass

class TaskFrameGroup(TaskFrame):

    def __new__(cls, argv, env):

        obj = super(TaskFrameGroup, cls).__new__(cls, argv, env)
        obj.depends = {}

        return obj

    def __len__(self):
        return len(self.depends)

    def add(self, instance, prev_instance):

        if instance not in self.depends:
            self.depends[instance] = []

        if prev_instance not in self.depends[instance]:
            self.depends[instance].append(prev_instance)

    def first_task(self):
        ftask = None
        for task, prev_task in self.depends.items():
            if ftask is None:
                ftask = task
            elif ftask == task:
                if prev_task is None:
                    return ftask
                else:
                    ftask = prev_task
        return ftask

    def last_task(self):
        ltask = None
        for task, prev_task in self.depends.items():
            if ltask is None:
                ltask = task
            elif ltask == prev_task:
                ltask = task
        return ltask

class SeqTaskFrameGroup(TaskFrameGroup):

    def __init__(self, argv, env):
        self.targs = self.parser.parse_args(argv)

    def perform(self):
        import pdb; pdb.set_trace()

def load_taskframe(taskname, config):

    if taskname in config.tasks:
        return config.tasks[taskname]
    else:
        import pdb; pdb.set_trace()

def build_taskgroup_from_argv(argv, env, config):

    # SeqTaskFrameGroup does not have its own argument
    taskgroup = SeqTaskFrameGroup([], dict(env))

    targv = []
    prev_instance = None

    for arg in argv:
        if arg == "--":
            if targv:
                task_frame = TaskFrame.load(targv[0], config)
                task_instance = task_frame(targv[1:], dict(env))
                taskgroup.add(task_instance, prev_instance)
                prev_instance = task_instance
            targv = []
        else:
            targv.append(arg)

    if targv:
        task_frame = TaskFrame.load(targv[0], config)
        task_instance = task_frame(targv[1:], dict(env))
        if task_instance:
            taskgroup.add(task_instance, prev_instance)
        else:
            import pdb; pdb.set_trace()

    if len(taskgroup) == 1:
        return taskgroup.first_task()
    else:
        return taskgroup
