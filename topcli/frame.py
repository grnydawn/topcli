# -*- coding: utf-8 -*-

"""Frame module."""

import os
import sys
import abc
import argparse

from .util import (PY3, name_match, envdict, is_taffile, extract_taffile,
    get_dest, get_nargs, get_action_name)

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

        if obj not in obj.parent.subframes:
            obj.parent.subframes.append(obj)

        return obj

    @abc.abstractmethod
    def __init__(self, *vargs):
        pass

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
                #frame = candidates.values()[0]
                _, frame = candidates.popitem()
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
                    return TafTaskFrameGroup(ctr, parent, npath, argv, newenv)
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
                        return TafTaskFrameGroup(ctr, parent, npath, argv, newenv)
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

    def __new__(cls, ctr, parent, turl, targv, env, *vargs):

        obj = super(TaskFrameGroup, cls).__new__(cls, ctr, parent, turl, targv, env)
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


class TafTaskFrameGroup(TaskFrameGroup):

    def __init__(self, ctr, parent, path, argv, env):

        def _parse(tobj, meta, sec, sid):

            # get dname and loc and nargs
            dinfo = eval(meta.get(sec, sid.strip()))
            sequal = [s.strip() for s in dinfo.split("=")]
            if len(sequal)==1:
                dname = sequal[0]
                sname = None
            elif len(sequal)==2:
                dname = sequal[0]
                sname = sequal[1]
            ssharp = dname.split("#")
            dest = get_dest(tobj.parser, ssharp[0])
            if len(ssharp)==1:
                loc = None
            elif len(ssharp)==2:
                loc = int(ssharp[1])

            return dest, loc, sname

        tmpdir = extract_taffile(path)

        meta = configparser.ConfigParser()
        with open(os.path.join(tmpdir, "METAFILE")) as mf:
            meta.readfp(mf)

        topts = {}
        tobjs = {}
        tdata = {}

        # create option name map
        optmap = {}
        for act in self.parser._actions:
            optmap[act.dest] = act.dest

        for option in meta.options("OPTION"):
            oid = option.split(".")[0]
            vargs, kwargs = self.teval_args(meta.get("OPTION", option))
            self.parser.add_argument(*vargs, **kwargs)
            dest = self.parser._actions[-1].dest
            optmap[dest] = oid

        # parser taf options
        self.targs = self.parser.parse_args(argv)

        # create taf option name to option value map
        gopts = dict((v, None) for v in optmap.values())

        for dest, value in self.targs._get_kwargs():
            gopts[optmap[dest]] = value

        # load tasks from taf
        for task in meta.options("TASK"):
            taskinfo = eval(meta.get("TASK", task))
            topts[task] = taskinfo[1:]
            tasktmp = TaskFrame.load(taskinfo[0], taskinfo[1:], ctr, parent, env)
            tobjs[task] = tasktmp
            tdata[task] = tasktmp.targs.data

        # replace task options
        # syntax: tid@rname#loc=gname
        for replace in meta.options("REPLACE"):
            rid = replace.split(".")[0]
            for tid, tops in topts.items():
                if rid == tid or rid == "*":

                    dest, loc, sname =  _parse(tobjs[tid], meta, "REPLACE", replace)
                    tparser = tobjs[tid].parser
                    action_name = get_action_name(tparser, dest)
                    nargs = get_nargs(tparser, dest)

                    if action_name == "_StoreAction":
                        pass
                        #import pdb; pdb.set_trace()
                    elif action_name == "_AppendAction":
                        pass
                        #import pdb; pdb.set_trace()
                    else:
                        import pdb; pdb.set_trace()


                    # skip options per loc
                    targets = []
                    ncnt = 0
                    for idx, top in enumerate(tops):
                        if (dest == "data" and tops[idx] in tdata[tid] and gopts[dest]) or \
                            optmap.get(get_dest(tparser, tops[idx]), None) == sname:
                            if loc is None or loc == ncnt:
                                targets.append(idx)
                            ncnt += 1

                    # replace options
                    rvalue = gopts[sname]

                    for target in sorted(targets):
                        if nargs is None:
                            if rvalue is not None:
                                tops[target+1] = rvalue
                        elif isinstance(nargs, int):
                            import pdb; pdb.set_trace()
                        elif nargs == "*":
                            end = len(tops)
                            for tidx, top in enumerate(tops[target+1:]):
                                if top.startswith("-"):
                                    end = tidx + target + 1
                                    break
                            tops[target:end] = rvalue
                        elif nargs == "+":
                            import pdb; pdb.set_trace()
                        elif nargs == "?":
                            import pdb; pdb.set_trace()
                        else:
                            import pdb; pdb.set_trace()

        # delete task options
        # syntax: tid@dname#loc
        dargs = [] # with location

        # TODO: set None to deleted items, and remove them later


        for delete in meta.options("DELETE"):
            did = delete.split(".")[0]
            for tid, tops in topts.items():
                if did == tid or did == "*":

                    dest, loc, sname =  _parse(tobjs[tid], meta, "DELETE", delete)
                    tparser = tobjs[tid].parser
                    action_name = get_action_name(tparser, dest)
                    nargs = get_nargs(tparser, dest)

                    if action_name == "_StoreAction":
                        pass
                        #import pdb; pdb.set_trace()
                    elif action_name == "_AppendAction":
                        pass
                        #import pdb; pdb.set_trace()
                    else:
                        import pdb; pdb.set_trace()

                    # skip options per loc
                    targets = []
                    ncnt = 0
                    for idx, top in enumerate(tops):
                        if get_dest(tparser, tops[idx]) == dest:
                            if loc is None or loc == ncnt:
                                targets.append(idx)
                            ncnt += 1

                    # delete options

                    for target in sorted(targets):
                        if nargs is None:
                            tops[target+1] = None
                        elif isinstance(nargs, int):
                            tops[target:target+nargs+1] = [None]*(nargs+1)
                        elif nargs == "*":
                            import pdb; pdb.set_trace()
                        elif nargs == "+":
                            import pdb; pdb.set_trace()
                        elif nargs == "?":
                            import pdb; pdb.set_trace()
                        else:
                            import pdb; pdb.set_trace()

        # append task options
        # syntax: tid@gname

        # TODO: append may not need option from --option option.
        for append in meta.options("APPEND"):
            aid = append.split(".")[0]
            for tid, tops in topts.items():
                if aid == tid or aid == "*":

                    dest, loc, sname =  _parse(tobjs[tid], meta, "APPEND", append)
                    tparser = tobjs[tid].parser
                    action_name = get_action_name(tparser, dest)
                    nargs = get_nargs(tparser, dest)

                    # this syntax does not have dest
                    sname = dest

                    if action_name == "_StoreAction":
                        pass
                        #import pdb; pdb.set_trace()
                    elif action_name == "_AppendAction":
                        pass
                        #import pdb; pdb.set_trace()
                    else:
                        import pdb; pdb.set_trace()

                    rvalue = gopts[sname]

                    # append options
                    if isinstance(rvalue, (list, tuple)):
                        tops.extend(rvalue)
                    else:
                        tops.append(rvalue)


        for tid, tops in topts.items():
            idx = 0
            while(idx < len(tops)):
                if tops[idx] is None:
                    tops.pop(idx)
                else:
                    idx += 1

        targvs = []
        for tid, tasktmp in sorted(tobjs.items()):
            targvs.append([tasktmp.turl] + topts[tid])

        next_instance = None

        for targv in reversed(targvs):
            task_instance = TaskFrame.load(targv[0], targv[1:], ctr, self, env)
            if task_instance:
                self.add(task_instance, next_instance)
                self.set_entryframe(task_instance)
                next_instance = task_instance


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

