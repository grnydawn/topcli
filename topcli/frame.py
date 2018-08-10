# -*- coding: utf-8 -*-

"""Frame module."""

import os
import sys
import abc
import argparse

from .util import (PY3, name_match, envdict, is_taffile, extract_taffile,
    dest_name, get_nargs)

if PY3:

    import importlib
    __import__ = importlib.__import__

    from urllib.request import urlopen
    from urllib.parse import urlparse
    from urllib.error import HTTPError, URLError

    import configparser
else:

    from urllib2 import urlopen, HTTPError, URLError
    from urlparse import urlparse

    import ConfigParser as configparser

class TaskFrame(object, ):

    __metaclass__ = abc.ABCMeta

    def __new__(cls, ctr, parent, url, argv, env):

        # TODO: wrap ArgumentParser to get inner info

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
        obj.turl = url
        obj.targv = list(argv)
        obj.targs = None
        obj.env = env
        obj.ctr = ctr
        obj.parent = parent
        obj.subframes = []

        return obj

    @abc.abstractmethod
    def __init__(self, ctr, parent, turl, argv, env):
        pass

    @classmethod
    def load_from_taf(cls, path, fragment, ctr, parent, argv, newenv):

        tmpdir = extract_taffile(path)

        meta = configparser.ConfigParser()
        with open(os.path.join(tmpdir, "METAFILE")) as mf:
            meta.readfp(mf)

        groupopts = {}
        taskopts = {}
        tasktmps = {}

        option = meta.options("OPTION")
        repace = meta.options("REPLACE")
        append = meta.options("APPEND")
        delete = meta.options("DELETE")

        for option in meta.options("OPTION"):
            groupopts[eval(option)] = eval(meta.get("OPTION", option))

        for task in meta.options("TASK"):
            tasknum = eval(task)
            taskinfo = eval(meta.get("TASK", task))
            taskopts[tasknum] = taskinfo[1:]
            tasktmp = cls.load(taskinfo[0], taskinfo[1:], ctr, parent, newenv)
            tasktmps[tasknum] = tasktmp

        for replace in meta.options("REPLACE"):
            rid = eval(replace)
            for tid, tops in taskopts.items():
                import pdb; pdb.set_trace()

        dargs = [] # with location
        for delete in meta.options("DELETE"):
            did = eval(delete)
            for tid, tops in taskopts.items():
                if did == tid or did == "*":
                    parser = tasktmps[tid].parser
                    dinfo = eval(meta.get("DELETE", delete))
                    for item in dinfo[0]:
                        split = item.split("#")
                        if len(split)==1:
                            dname = split[0]
                            loc = None
                        elif len(split)==2:
                            dname = split[0]
                            loc = int(split[1])
                        dest = dest_name(dname)
                        nargs = get_nargs(parser, dest)
                        idx = 0
                        lcnt = 0 
                        ncnt = 0 
                        while(idx<len(tops)):

                            if ncnt is None:
                                pass
                            elif isinstance(ncnt, int) and ncnt > 0:
                                tops.pop(idx)
                                ncnt -= 1
                                continue
                            elif ncnt == "*":
                                if tops[idx].startswith("-"):
                                    ncnt = None
                                else:
                                    tops.pop(idx)
                                    continue
                            elif ncnt == "+":
                                tops.pop(idx)
                                ncnt = "*"
                                continue
                            elif ncnt == "?":
                                if tops[idx].startswith("-"):
                                    ncnt = None
                                else:
                                    tops.pop(idx)
                                    ncnt = None
                                    continue


                            if dest_name(tops[idx]) == dest:
                                lcnt += 1
                                if loc is None or loc == lcnt:
                                    tops.pop(idx)
                                    ncnt = nargs
                                else:
                                    idx += 1
                            else:
                                idx += 1
        
        for append in meta.options("APPEND"):
            aid = eval(append)
            for tid, tops in taskopts.items():
                import pdb; pdb.set_trace()

        targvs = []
        for tid, tasktmp in tasktmps.items():
            targvs.append([tasktmp.turl] + taskopts[tid])

        return ShellTaskFrameGroup(ctr, parent, path, targvs, newenv)

    @classmethod
    def load_from_path(cls, path, fragment, ctr, parent, argv, newenv):
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
                frame = candidates.get(fragment, None)
            elif len(candidates) == 1:
                frame = candidates.values()[0]
            else:
                import pdb; pdb.set_trace()

            return frame(ctr, parent, path, argv, newenv)

    @classmethod
    def load(cls, url, argv, ctr, parent, env):
        o = urlparse(url)

        newenv = envdict()
        newenv.parent = env

        if o.netloc:
            import pdb; pdb.set_trace()
        elif o.path:
            # local path
            if os.path.exists(o.path):
                npath = os.path.abspath(os.path.realpath(o.path))
                if is_taffile(npath):
                    return cls.load_from_taf(npath, o.fragment,
                        ctr, parent, argv, newenv)
                else:
                    return cls.load_from_path(npath, o.fragment,
                        ctr, parent, argv, newenv)

            # loaded task
            if o.path in ctr.config.tasks:
                frame = ctr.config.tasks[o.path]
                return frame(ctr, parent, o.path, argv, newenv)

            # installed task
            if o.path in ctr.config.taskconfig["names"]:
                if os.path.exists(ctr.config.taskconfig["names"][o.path]):
                    npath = ctr.config.taskconfig["names"][o.path]
                    npath = os.path.abspath(npath)
                    if is_taffile(npath):
                        return cls.load_from_taf(npath, o.fragment, ctr, parent, argv, newenv)
                    else:
                        return cls.load_from_path(npath, o.fragment, ctr, parent, argv, newenv)
                else:
                    import pdb; pdb.set_trace()

            # shorten name match with loaded tasks
            match = name_match(o.path, ctr.config.tasks.keys())
            if match:
                import pdb; pdb.set_trace()

            # shorten name match with installed tasks
            match = name_match(o.path, ctr.config.taskconfig["names"].keys())
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
        if self.targs.data:
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

    def teval_args(self, argv, **kwargs):

        def _p(*argv, **kw_str):
            return list(argv), kw_str

        return self.teval('_p(%s)'%argv, _p=_p, **kwargs)

    def teval_atargs(self, expr, **kwargs):
        s = [i.strip() for i in expr.split("@")]
        v, k = self.teval_args(s[-1], **kwargs)
        return s[:-1], v, k

    def teval_func(self, func, *vargs, **kwargs):

        return self.teval('_f_(*_v_, **_k_)', _f_=func,
            _v_=vargs, _k_=kwargs)

    def parse_args(self, expr):

        def _unstrmap(text, strmap):

            for k, v in strmap.items():
                text = text.replace(k, v)

            return text

        def _strmap(text):
            strmap = {}

            quote = None
            out = []
            buf = []
            for ch in text:
                if ch=='"' or ch=="'":
                    if quote:
                        if quote==ch:
                            strid = "topclistrmap%d"%len(strmap)
                            out.append(strid)
                            strmap[strid] = "".join(buf)
                            out.append(quote)

                            buf = []
                            quote = None
                        else:
                            buf.append(ch)
                    else:
                        quote = ch
                        out.append(quote)
                elif quote:
                    buf.append(ch)
                else:
                    out.append(ch)

            return "".join(out), strmap


        lv = []
        lk = {}

        newtext, strmap = _strmap(expr)

        for item in [i.strip() for i in newtext.split(',')]:
            if '=' in item:
                new, old = [i.strip() for i in item.split('=')]
                lk[new] = _unstrmap(old, strmap)
            else:
                lv.append(_unstrmap(item, strmap))

        return lv, lk

class TaskFrameUnit(TaskFrame):
    pass

class TaskFrameGroup(TaskFrame):

    def __new__(cls, ctr, parent, turl, argv, env):

        obj = super(TaskFrameGroup, cls).__new__(cls, ctr, parent, turl, argv, env)
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


class ShellTaskFrameGroup(TaskFrameGroup):

    def __init__(self, ctr, parent, url, targvs, env):

        self.targs = self.parser.parse_args([])

        next_instance = None

        for targv in reversed(targvs):
            task_instance = TaskFrame.load(targv[0], targv[1:], ctr, self, env)
            if task_instance:
                self.add(task_instance, next_instance)
                self.set_entryframe(task_instance)
                next_instance = task_instance

#            task_frame, remained = TaskFrame.load(targv[0], ctr.config)
#            if task_frame is not None:
#                newenv = envdict()
#                newenv.parent = env
#                if task_frame is TafTaskFrameGroup:
#                    task_instance = task_frame(ctr, self, remained[0], remained[1], newenv)
#                else:
#                    task_instance = task_frame(ctr, self, remained, targv[1:], newenv)
#                if task_instance is not None:

