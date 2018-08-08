# -*- coding: utf-8 -*-

"""Frame module."""

import abc
import argparse

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

        parser.add_argument('data', nargs='*', help='input data.')

        obj = super(TaskFrame, cls).__new__(cls)
        obj.parser = parser
        obj.targs = None

        return obj

    @abc.abstractmethod
    def __init__(self, argv):
        pass

    def run(self, env):

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

def build_taskgroup_from_argv(argv):

    # SeqTaskFrameGroup does not have its own argument
    taskgroup = SeqTaskFrameGroup([])

    targv = []
    prev_instance = None

    for arg in argv:
        if arg == "--":
            if targv:
                taskframe = load_taskframe(targv[0])
                taskinstance = taskframe(targv[1:])
                taskgroup.add(taskinstance, prev_instance)
                prev_instance = taskinstance
            targv = []
        else:
            targv.append(arg)

    if targv:
        taskframe = load_taskframe(targv[0])
        taskinstance = taskframe(targv[1:])
        taskgroup.add(taskinstance, prev_instance)

    return taskgroup
