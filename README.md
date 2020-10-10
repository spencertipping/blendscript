# BlendScript: nondestructive precision Blender automation
BlendScript is a small functional programming language designed for ergnonomic,
repeatable editing in Blender. Where possible it uses the same number of
keystrokes as the UI would require, and it's designed to be run in a live Python
editor with the source embedded as a raw string:

```py
import blendscript
blendscript.live_run(r'''
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
