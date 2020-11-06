# Optimization
As of `8a86795f7fde1181073dc908e7626a7b4e5e8cc0`, BlendScript takes just over 3s
to run 780 lines of code. That makes it a little too slow to use for interactive
work. We'll do better if we can save some work.

BlendScript has a few problems that cause it to be slower than it should be:

1. Parse data can't be reused
2. There is no module system (an example of (1))
3. Blender objects are emitted as side-effects, not in a structured way
4. Let-bindings are implemented inefficiently
5. Blender objects can't be reused; everything is redone from scratch


## Strategies
90% of our time is spent parsing and compiling. It's difficult to say where the
hotspots are within that process because the compiler is interleaved with the
parser; here's the top of `cProfile` output for my test script:

```
         15261803 function calls (11239862 primitive calls) in 5.514 seconds

   Ordered by: internal time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
1510308/6    1.145    0.000    5.146    0.858 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:112(__call__)
  1865708    1.124    0.000    1.637    0.000 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:60(f)
 615960/2    0.528    0.000    5.146    2.573 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:87(f)
 614839/1    0.412    0.000    5.146    5.146 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:213(f)
  4571820    0.364    0.000    0.364    0.000 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:27(fail)
  1865708    0.343    0.000    0.343    0.000 {method 'match' of 're.Pattern' objects}
613725/613176    0.302    0.000    3.091    0.000 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:249(f)
 596344/4    0.275    0.000    5.145    1.286 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:178(__call__)
 650624/1    0.246    0.000    5.146    5.146 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:261(g)
5555/3910    0.121    0.000    4.271    0.001 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:146(__call__)
   635488    0.061    0.000    0.061    0.000 {method 'append' of 'list' objects}
   624277    0.059    0.000    0.059    0.000 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/parsers/peg.py:28(ok)
        3    0.052    0.017    0.052    0.017 {built-in method _bpy.ops.call}
     1765    0.043    0.000    0.043    0.000 {built-in method builtins.compile}
643156/643152    0.042    0.000    0.042    0.000 {built-in method builtins.len}
       14    0.040    0.003    0.040    0.003 /home/spencertipping/.config/blender/2.82/scripts/addons/blendscript/blender/bmesh.py:292(spin)
```

After poking around a bit I don't think we can get very much mileage from
optimizing the parser. We might be able to get 500ms by inlining every `ok` and
`fail`, but we're making too many calls for it ever to be very fast.

The most effective strategies are likely to be higher-level: parse less code per
iteration and reuse parse output where we can. Incremental parsing is probably a
non-starter because the language is so compact; changing one character will
potentially change everything downstream, with very little in the way of
reliable sentinels to bound the change. (And it's a lot of work to memoize a PEG
parser this way.)


## Modules and a parse cache
Right now we have a single entry point that starts from scratch:

```py
import blendscript
blendscript.live(r'''
:a 1
:b 2

[
  b<"foo m<[cva b 3],
  # 700 lines of other code...
]
''')
```

If we wanted to split the 700LOC list into multiple pieces, we'd need to (1)
parcel out the GC to make sure we collect only one piece at a time; and (2) have
a way to make global definitions visible to multiple modules (and manage the
parse dependency).

(2) involves splitting the code into two grammars: one to define stuff and one
to generate Blender output. The define-stuff grammar would produce a scope
object containing precompiled values that would get bound up as
compile-transient gensyms.
