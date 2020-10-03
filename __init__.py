"""
Blender scripting language with a focus on brevity.

The goal is to make it possible to drive Blender using just a script and using
fewer keystrokes than you'd use against the normal UI. This library is oriented
towards CAD, engineering, and precision editing. It's largely imperative, just
like Blender's scripting API.
"""

from .parsers import parse

go = parse
