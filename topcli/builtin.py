# -*- coding: utf-8 -*-

"""builtin task module."""

from .frame import TaskFrameUnit

class GroupTaskFrame(TaskFrameUnit):

    def __init__(self, ctr, parent, argv, env):

        # map grouptask option to subtask option

        self.parser.add_argument('-m', '--map', metavar='mapping', action='append', help='option mapping.')

        self.targs = self.parser.parse_args(argv)

        if len(self.targs.data) != 1:
            self.error_exit("'group' task requires one positional argument.")

        self.group_name = self.targs.data.pop()

    def perform(self):

        optmap = {}

        if self.targs.map:
            for m in self.targs.map:
                s = m.split("@")
                if len(s) == 2:
                    vargs, kwargs = self.parse_args(s[1])
                    optmap[int(s[0])] = kwargs
                else:
                    self.error_exit("Wrong syntax near '%s'."%m)

        # TODO: construct command line options and save in zip file

#        frame = self
#        idx = 0
#        while frame:
#            idx += 1
#            frame = self.parent.depends[frame]
#            if frame and idx in optmap:
#                import pdb; pdb.set_trace()

builtin_taskframes = {
    "group":      GroupTaskFrame,
}
