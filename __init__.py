"""
Blender scripting language with a focus on brevity
==================================================

The goal is to make it possible to drive Blender using just a script and using
fewer keystrokes than you'd use against the normal UI. This library is oriented
towards CAD, engineering, and precision editing.

BlendScript is largely expression-driven and is parsed using combinatory PEG.
"""

import bpy

from .parsers import expr


bl_info = {
  "name": "BlendScript",
  "blender": (2, 80, 0),
  "category": "Development",
}


def compile(source):
  """
  Compiles the specified BlendScript source, throwing an error or returning a
  Python function. The resulting function can be invoked on no arguments to
  execute it, or you can provide a single expr_eval_state object to override
  the evaluation state.
  """
  if type(source) == str: source = source.encode()
  f, i = expr.compiled_expr(source, 0)

  if i is None: raise Exception(
    f'blendscript.compile(): failed to parse {source}')

  if i != len(source): raise Exception(
    f'blendscript.compile(): failed to parse beyond {i}: {source[i:]}')

  return f

def run(source):
  """
  Runs the given source directly. This is a shorthand for compile(source)().
  """
  return compile(source)()


class BlendScriptOp(bpy.types.Operator):
  bl_idname  = "text.run_blendscript"
  bl_label   = "Run BlendScript"
  bl_options = {'REGISTER'}

  def execute(self, context):
    print('Running BlendScript...')
    print(run(context.space_data.text.as_string()))
    return {'FINISHED'}


addon_keymaps = []

def register():
  bpy.utils.register_class(BlendScriptOp)

  # Add the hotkey
  wm = bpy.context.window_manager
  kc = wm.keyconfigs.addon
  if kc:
    km = wm.keyconfigs.addon.keymaps.new(name='Text', space_type='TEXT_EDITOR')
    kmi = km.keymap_items.new(BlendScriptOp.bl_idname, type='B', value='PRESS', alt=True)
    addon_keymaps.append((km, kmi))

  bpy.types.TEXT_MT_text.append(
    lambda self, context: self.layout.operator(BlendScriptOp.bl_idname))

def unregister():
  bpy.utils.unregister_class(BlendScriptOp)

  # Remove the hotkey
  for km, kmi in addon_keymaps:
    km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == '__main__':
  register()
