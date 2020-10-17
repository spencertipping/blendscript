import blendscript
import sys

if sys.stdin.isatty():
  blendscript.repl()
else:
  t, v = blendscript.run(sys.stdin.read())
  print(f'{v} :: {t}')
