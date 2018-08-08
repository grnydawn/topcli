#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `topcli` package."""

import pytest


from topcli import main

def test_noarg():
    output = main([])
    assert 'Hello' in output
