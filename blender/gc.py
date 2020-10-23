"""
Automatic removal of obsolete objects, and content hashing for memoization.
"""

from ..compatibility import *


try:
  import bpy

  def gc_tag(o):
    o['blendscript/gc'] = True
    return o

  def gc(collection, live_set=set()):
    for o in collection:
      if o.get('blendscript/gc') is not None and o not in live_set:
        collection.remove(o)

  def add_hashed(collection, source, generator):
    name = f'_{abs(hash(source)):016x}'

    # TODO: figure out why memoizing this function results in unstable output
    # in Blender. Uncommenting the next line does the right thing 90% of the
    # time, but the other 10% associates objects incorrectly.
    #
    # if name in collection: return collection[name]

    return gc_tag(generator(source, name))


except ModuleNotFoundError:
  blender_not_found()
