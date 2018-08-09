# -*- coding: utf-8 -*-

"""print task module."""

import topcli

class PrintTask(topcli.TaskFrameUnit):

    def __init__(self, ctr, parent, argv, env):

        self.parser.add_argument('--str', metavar='variable', nargs=1, help='generate string.')
        self.parser.add_argument('--version', action='version', version='print task version 0.1.0')

        self.targs = self.parser.parse_args(argv)

        try:
            import numpy
            self.env["numpy"] = self.env["np"] = numpy
        except ImportError as err:
            pass

        try:
            import pandas
            self.env["pandas"] = self.env["pd"] = pandas
        except ImportError as err:
            pass

    def perform(self):

        printed = False

        # pages setting
        if self.targs.str:
            for str_arg in self.targs.str:
                print(self.teval(str_arg))
                printed = True

        if not printed:
            print(self.env["D"])

        return 0
