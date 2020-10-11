# BlendScript: nondestructive precision Blender automation
BlendScript is a small functional programming language designed for ergnonomic,
repeatable editing in Blender. Where possible it uses the same number of
keystrokes as the UI would require, and it's designed to be run in a live Python
editor with the source embedded as a raw string:

```py
import blendscript
blendscript.live(r'''
# your code here
''')
```


## Language structure
BlendScript's operators use Łukasiewicz notation (prefix notation, the opposite
of stack-oriented Reverse Polish Notation) and support automatic currying and
sections, just like operator sections in Haskell. Parentheses are optional; when
present, they provide a Lisp-style syntax:

```
+ 3 * 4 5           # no parens required
(+ 3 (* 4 5))       # same thing, with parens
```

Because BlendScript is an interactive language, it uses parse failure as an
internal mechanism to select alternatives but generally doesn't propagate this
failure upwards as a syntax or runtime error. For example, `+ 3 * 4` produces
`7` despite the fact that `* 4` would normally be parsed as a function.


## Control flow and side effects
Concatenative via list reduction against a mutable Blender context/env/thing.
Side effects are objects that modify something when applied to it.

Side-effecting objects -- i.e. functions that transform stateful values -- are
constructed using syntax that closely corresponds to Blender's keyboard
shortcuts.


## Mesh operations
Let's golf a few basic mesh construction scenarios.

+ Creating things
  + Cube from vertex: 14 `ex2\n aey2\n aez2\n`
  + Cylinder from circle: 5 `fez2\n`
  + 2x4" from cube: 18 `sx.75\n sy1.75\n sz48\n`

Creating a chain link isn't easy at all using just the keyboard. To my knowledge
there isn't an easy way to manage vertex selections. Maybe we count mouse ops as
equivalent to some number of keystrokes?


## Vertex, edge, and face selection
We'll want various query structures that let us emulate what you can do with the
mouse, but using commands instead. We can use things like extrusion/selection
history, select-by-bounds, select by distance, etc.

**Q:** does `bmesh` export a proportional-editor API? (no, but we could make
one)


## Fast mesh regen
We can hash the operation stream used to generate each mesh. Then the mesh
function can check for the existence of the desired object and skip if it's
already there. This will require us to implement some type of hashing for lists,
which I don't think will be a problem.


## Multi-context expr parsing
We have mesh-edit context, object context, etc. Each of these can be an `alt()`
that stacks a DSL onto generic expressions, possibly propagating itself through
containers like lists.
