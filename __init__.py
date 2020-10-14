"""
Blender scripting language with a focus on brevity
==================================================

The goal is to make it possible to drive Blender using just a script and using
fewer keystrokes than you'd use against the normal UI. This library is oriented
towards CAD, engineering, and precision editing.

BlendScript is largely expression-driven and is parsed using combinatory PEG.
"""

from time import time

from .parsers import expr


bl_info = {
  "name": "BlendScript",
  "blender": (2, 80, 0),
  "category": "Development",
}


def compile(source, debug=False):
  """
  Compiles the specified BlendScript source, throwing an error or returning a
  Python function. The resulting function can be invoked on no arguments to
  execute it, or you can provide a single expr_eval_state object to override
  the evaluation state.
  """
  t0 = time()
  if type(source) == str: source = source.encode()
  f, i = expr.compiled_expr(source, 0)
  if i is None: raise Exception(
    f'blendscript.compile(): failed to parse {source}')
  if i != len(source): raise Exception(
    f'blendscript.compile(): failed to parse beyond {i}: {source[i:]}')
  t1 = time()

  if t1 - t0 > 0.1:
    print(f'{t1 - t0} second(s) to parse+compile script {source}')

  if debug: print(f"compiled blendscript to function: {f}")
  return f

def run(source, **kwargs):
  """
  Runs the given source directly. This is a shorthand for compile(source)().
  """
  return compile(source, **kwargs)()

def live(source, **kwargs):
  """
  Runs the given source directly. In the future this will do some automatic
  Blender object management to make it easier to work with generated objects.
  """
  t0 = time()
  r  = run(source, **kwargs)
  t1 = time()
  print(f'blendscript: {int(1000 * (t1 - t0))}ms> {r}')
  return r
