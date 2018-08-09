# -*- coding: utf-8 -*-

"""builtin task module."""

from .frame import TaskFrameUnit

#class TryTaskFrame(TaskFrameUnit):
#
#    def __init__(self, argv):
#
#        self.parser.add_argument('taskloc', help='location of taskframe.')
#
#        targs, remained = self.parser.parse_known_args(argv)
#        taskframe = self.load_taskframe(targs)
#        import pdb; pdb.set_trace()
#
#    def perform(self, env):
#        import pdb; pdb.set_trace()

builtin_taskframes = {
#    "try":      TryTaskFrame,
}
