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

You can also run an offline REPL without loading Blender-specific libraries:

```sh
$ ./repl -c '/+[1,2,3]'
6
$ ./repl
>>> f(+7) L*fi5
[7, 8, 9, 10, 11] :: ([] .) (2ms)
>>>
```

...and for debugging the language itself, you can run a Python repl with
preloaded imports:

```sh
$ ./repl -p
>>> val_expr(b'+ 3 4', 0)
```


## Language structure
BlendScript's operators use Łukasiewicz notation (prefix notation, the opposite
of stack-oriented Reverse Polish Notation) and support automatic currying and
sections, just like operator sections in Haskell. Parentheses are often
optional; when present, they provide a Lisp-style syntax:

```
+ 3 * 4 5           # no parens required
(+ 3 (* 4 5))       # same thing, with parens
```

This works because BlendScript uses type information to try to figure out how to
fold things up when it appears to be ambiguous. (We'll eventually have a variant
of Hindley-Milner; for now it's partially typed and often falls back to
dynamic/unknown types.)

`let`-bindings are achieved by writing an unbound identifier followed by a
value; the value immediately following such a binding will be parsed within a
lexical scope that binds the name you provided:

```
>>> f (+ 1) f 5
6
>>> :f (+ 1) f 5        # explicit : operator
6
```


## Builtin functions
**TODO:** document this

...for now, you can check out [runtime/val.py](runtime/val.py).
