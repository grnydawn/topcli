# -*- coding: utf-8 -*-

"""Main module."""

import sys

from .frame import build_taskgroup_from_argv
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

    env = {"__builtins__": __builtins__}

    taskframe = build_taskgroup_from_argv(argv, env, config)
    taskcontroller = TaskController(taskframe, config)
    retval = taskcontroller.run()

    config.dump()

    return retval

