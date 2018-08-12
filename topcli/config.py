# -*- coding: utf-8 -*-

"""Config module."""

import os
import json

class Config(object):

    metafile = "METAFILE"
    histfile = "HISTFILE"

    def __init__(self):

        self.paths = {}

        homedir = os.path.join(os.path.expanduser("~"), ".topcli")
        self.paths['homedir'] = homedir

        # home directory
        if not os.path.isdir(homedir):
            os.makedirs(homedir)

        metafile = os.path.join(homedir, self.metafile)
        if not os.path.isfile(metafile):
            metadata = {"version": "0.1.0"} # top metadata
            with open(metafile, 'w') as f:
                json.dump(metadata, f, indent=4)

        self.paths["topconfig"] = metafile
        with open(metafile, 'r') as f:
            self.topconfig = json.load(f)

        # task directory
        taskdir = os.path.join(homedir, "task")
        self.paths['taskdir'] = taskdir
        if not os.path.isdir(taskdir):
            os.makedirs(taskdir)

        metafile = os.path.join(taskdir, self.metafile)
        if not os.path.isfile(metafile):
            metadata = {"__test__": 1} # task metadata
            with open(metafile, 'w') as f:
                json.dump(metadata, f, indent=4)

        self.paths["taskconfig"] = metafile
        with open(metafile, 'r') as f:
            self.taskconfig = json.load(f)

        # installed tasks
        if "names" not in self.taskconfig:
            self.taskconfig["names"] = {}

        # defined aliases
        if "aliases" not in self.taskconfig:
            self.taskconfig["aliases"] = {}

        self.tasks = {}

        histfile = os.path.join(homedir, self.histfile)
        if not os.path.isfile(histfile):
            histdata = {"list": []}
            with open(histfile, 'w') as f:
                json.dump(histdata, f, indent=4)

        self.paths["histconfig"] = histfile
        with open(histfile, 'r') as f:
            self.histconfig = json.load(f)

#        for entry in os.listdir(taskdir):
#            taskpath = os.path.join(taskdir, entry)
#            if taskpath == metafile:
#                pass
#            elif os.path.isdir(taskpath):
#                self.tasks[taskpath] = None # not loaded
#            elif os.path.isfile(taskpath):
#                self.tasks[taskpath] = None # not loaded
#            else:
#                import pdb; pdb.set_trace()

    def dump(self):

        with open(self.paths["topconfig"], 'w') as f:
            json.dump(self.topconfig, f, indent=4)

        with open(self.paths["taskconfig"], 'w') as f:
            json.dump(self.taskconfig, f, indent=4)

        with open(self.paths["histconfig"], 'w') as f:
            json.dump(self.histconfig, f, indent=4)
