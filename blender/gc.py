"""
Automatic removal of obsolete objects.
"""


try:
  import bpy

  def gc_tag(o):
    o['blendscript/gc'] = True
    return o

  def gc(collection, live_set=set()):
    for o in collection:
      if o.get('blendscript/gc') is not None and o not in live_set:
        collection.remove(o)

except ModuleNotFoundError:
  pass
