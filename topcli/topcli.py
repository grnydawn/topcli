# -*- coding: utf-8 -*-

"""Main module."""

import sys

from .frame import SeqTaskFrameGroup, TaskFrame
from .controller import TaskController
from .config import Config
from .builtin import builtin_taskframes

def entry():
    return main(sys.argv[1:])

def main(argv):

    def _show_usage():
        print("Usage: perform task [arguments ...] [ -- task [arguments ...]] ...")

    # handle entry options
    if not argv or argv[0] in ("-h", "--help"):
        _show_usage()
        sys.exit(0)
    elif argv[0] == "--version":
        print("perform version 0.1.0")
        sys.exit(0)

    config = Config()

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
    env = {"__builtins__": __builtins__}

    if len(gargv) > 1:
        instance = SeqTaskFrameGroup(ctr, ctr, gargv, env)
    elif targv:
        task_frame = TaskFrame.load(targv[0], config)
        instance = task_frame(ctr, ctr, targv[1:], env)

    retval = ctr.run(instance)

    config.dump()

    return retval
