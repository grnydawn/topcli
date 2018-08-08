# -*- coding: utf-8 -*-

"""Main module."""

import sys

def entry():
    main(sys.argv[1:])

def main(argv):

    def show_usage():
        print("Usage: perform task [input [input ...]] [option [option ...]] [ -- task ...]")

    # handle entry options
    if not argv or argv[0] in ("-h", "--help"):
        show_usage()
        sys.exit(0)
    elif argv[0] == "--version":
        print("perform version 0.1.0")
        sys.exit(0)

    # perform task(s)
    from .perform import perform_task
    return perform_task(argv)

