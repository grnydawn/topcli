# -*- coding: utf-8 -*-

"""Perform module."""
 
class TaskController(object):

    def __init__(self, config):
        self.config = config
        self.subframes = []

    def register(self, frame):

        self.subframes.append(frame)

    def run(self, instance):

        return instance.run()
