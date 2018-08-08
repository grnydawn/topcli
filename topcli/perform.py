# -*- coding: utf-8 -*-

"""Perform module."""

from .frame import build_taskgroup_from_argv
from .controller import TaskController
 
def perform_task(argv):

    taskframe = build_taskgroup_from_argv(argv)
    taskcontroller = TaskController(taskframe)
    return taskcontroller.run()

