"""
Blender scripting language with a focus on brevity
==================================================

The goal is to make it possible to drive Blender using just a script and using
fewer keystrokes than you'd use against the normal UI. This library is oriented
towards CAD, engineering, and precision editing.

BlendScript is largely expression-driven and is parsed using combinatory PEG.
"""

import traceback
from time import time
from sys  import stdin

from .parsers.peg     import pmap
from .parsers.val     import val_expr
from .parsers.bmesh   import *
from .parsers.bobject import *

from .blender.gc          import *
from .runtime.val         import *
from .runtime.blendermath import *


try:
  import bpy
  def gc_objects(): gc(bpy.data.objects)

except ModuleNotFoundError:
  def gc_objects(): pass


bl_info = {
  "name": "BlendScript",
  "blender": (2, 80, 0),
  "category": "Development",
}


def register():   pass
def unregister(): pass


def compile(source, debug=False):
  """
  Compiles the specified BlendScript source, throwing an error or returning a
  Python function. The resulting function can be invoked on no arguments to
  execute it, or you can provide a single expr_eval_state object to override
  the evaluation state.
  """
  t0 = time()
  if type(source) == str: source = source.encode()
  v, i = val_expr(source, 0)

  if i is None: raise SyntaxError(
    f'blendscript.compile(): failed to parse {source}')
  if i != len(source): raise SyntaxError(
    f'blendscript.compile(): failed to parse beyond {i}: {source[i:]}')

  if debug: print(f'-> {v}')
  f = (v.t, v.compile())
  t1 = time()

  if t1 - t0 > 0.1:
    print(f'{t1 - t0} second(s) to parse+compile script {source}')

  return f


def run(source, **kwargs):
  """
  Runs the given source directly. This is a shorthand for compile(source)().
  """
  try:
    ft, f = compile(source, **kwargs)
    gc_objects()
    v = f()
  finally:
    blender_refresh_view()
  return (ft, v)


def live(source, **kwargs):
  """
  Runs the given source directly. In the future this will do some automatic
  Blender object management to make it easier to work with generated objects.
  """
  t0 = time()
  r  = run(source, **kwargs)[1]
  t1 = time()
  print(f'blendscript: {int(1000 * (t1 - t0))}ms> {r}')
  return r


def repl():
  """
  Runs a repl between stdin and stdout.
  """
  lines = []
  while True:
    try:
      lines.append(input('>>> ' if len(lines) == 0 else '... '))
      try:
        t0 = time()
        t, v = run("".join(lines))
        t1 = time()
        print(f'{v} :: {t} ({int((t1 - t0) * 1000)}ms)')
        lines = []
      except SyntaxError:
        # Assume we're collecting more lines of input
        pass
      except Exception as e:
        print(f'error: {e}')
        print(traceback.format_exc())
        lines = []

    except EOFError:
      if len(lines):
        print()
        lines = []
        continue
      else:
        print()
        break

    except KeyboardInterrupt:
      print()
      lines = []
