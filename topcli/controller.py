# -*- coding: utf-8 -*-

"""Perform module."""
 
class TaskController(object):

    def __init__(self, taskframe, config):
        self.frame = taskframe
        self.config = config

    def run(self):
        env = {}
        self.frame.run(self, env)
