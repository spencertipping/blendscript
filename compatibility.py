"""
A function to complain if we don't have stuff.
"""

import sys

already_printed = False

def blender_not_found():
  global already_printed
  if not already_printed:
    print('warning: Blender APIs not available', file=sys.stderr)
  already_printed = True
