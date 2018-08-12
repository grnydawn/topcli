# -*- coding: utf-8 -*-

"""Main module."""

import sys

from .frame import ShellTaskFrameGroup, TaskFrame
from .controller import TaskController
from .config import Config
from .builtin import builtin_taskframes
from .util import envdict

import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

def entry():
    return main(sys.argv[1:])

def main(argv):

    def _show_usage():
        # TODO: may use textwrap dedent
        print("perform version 0.1.0")
        print("Usage: perform <task> [arguments] [-- <task> [arguments]] ...")

    # handle entry options
    if not argv or argv[0] in ("-h", "--help"):
        _show_usage()
        sys.exit(0)
    elif argv[0] == "--version":
        print("perform version 0.1.0")
        sys.exit(0)

    config = Config()

    if argv and len(argv) > 0 and argv[0] != "history":
        config.histconfig["list"].append(argv)

    if argv and len(argv) > 1 and argv[0] == "history" and argv[1].isdigit():
        argv = config.histconfig["list"][int(argv[int(argv[1].isdigit())])]

    # load builtin tasks
    config.tasks.update(builtin_taskframes)

    gargv = []
    targv = []

    for arg in argv:
        if arg == "--":
            if targv:
                gargv.append(targv)
            targv = []
        else:
            targv.append(arg)

    if targv:
        gargv.append(targv)

    ctr = TaskController(config)

    env = envdict()
    env["__builtins__"] =  __builtins__

    if len(gargv) > 1:
        instance = ShellTaskFrameGroup(ctr, ctr, "", gargv, env)
    elif targv:
        instance = TaskFrame.load(targv[0], targv[1:], ctr, ctr, env)

    if instance:
        retval = ctr.run(instance)
    else:
        print("ERROR: execution failed.")
        retval = -1

    config.dump()

    return retval
