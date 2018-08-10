# -*- coding: utf-8 -*-

"""Frame module."""

import os
import sys
import abc
import argparse

from .util import PY3, name_match, envdict

if PY3:

    import importlib
    __import__ = importlib.__import__

    from urllib.request import urlopen
    from urllib.parse import urlparse
    from urllib.error import HTTPError, URLError

else:

    from urllib2 import urlopen, HTTPError, URLError
    from urlparse import urlparse

class TaskFrame(object, ):

    __metaclass__ = abc.ABCMeta

    def __new__(cls, ctr, parent, args, env):

        parser = argparse.ArgumentParser()

        parser.add_argument('data', metavar='<input data>', nargs="*", help='input data')

#        parser.add_argument('--import-task', metavar='task', action='append', help='import task')
#        parser.add_argument('--import-function', metavar='function', action='append', help='import function')
#        parser.add_argument('--import-module', metavar='module', action='append', help='import module')
        parser.add_argument('--promote', metavar='variable', action='append', help='promote local varialble to global level.')
        parser.add_argument('--calc', metavar='calc', action='append', help='python code for manipulating data.')
#        parser.add_argument('--output', metavar='output', action='append', help='output variable.')

        obj = super(TaskFrame, cls).__new__(cls)
        obj.parser = parser
        obj.targs = None
        obj.env = env
        obj.ctr = ctr
        obj.parent = parent
        obj.subframes = []

        return obj

    @abc.abstractmethod
    def __init__(self, ctr, parent, args, env):
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

    def register(self, frame):

        self.subframes.append(frame)

    def run(self):

        if self not in self.parent.subframes:
            self.parent.subframes.append(self)

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
        out = self.perform()

        if self.targs.promote:
            for promote_arg in self.targs.promote:
                vargs, kwargs = self.teval_args(promote_arg)
                self.parent.env.update(kwargs)

        return out

    @abc.abstractmethod
    def perform(self):
        pass

    def error_exit(self, msg):
        # TODO: coordinate with self.ctr

        print("ERROR: "+msg)
        sys.exit(-1)

    def teval(self, expr, **kwargs):
        try:
            env = dict((k,v) for k,v in self.env.items())
            return eval(expr, env, kwargs)
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

    def __new__(cls, ctr, parent, args, env):

        obj = super(TaskFrameGroup, cls).__new__(cls, ctr, parent, args, env)
        obj.depends = {}
        obj.entryframe = None

        return obj

    def __len__(self):
        return len(self.depends)

    def add(self, instance, next_instance):

        if instance not in self.depends:
            self.depends[instance] = next_instance
        else:
            self.error_exit("taskframe is already used.")

    def set_entryframe(self, frame):
        self.entryframe = frame

    def perform(self):
        pass

    def run(self):

        frame = self.entryframe

        out = -1
        while(frame):
            # TODO: how to merge envs
            out = frame.run()
            frame = self.depends[frame]

        return out

class SeqTaskFrameGroup(TaskFrameGroup):

    def __init__(self, ctr, parent, targvs, env):

        self.targs = self.parser.parse_args([])

        next_instance = None

        for targv in reversed(targvs):
            task_frame = TaskFrame.load(targv[0], ctr.config)
            if task_frame is not None:
                newenv = envdict()
                newenv.parent = env
                task_instance = task_frame(ctr, self, targv[1:], newenv)
                if task_instance is not None:
                    self.add(task_instance, next_instance)
                    self.set_entryframe(task_instance)
                    next_instance = task_instance

