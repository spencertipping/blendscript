"""
REPL setup script for BlendScript.

This is used by ./repl -p to create a REPL environment with preloaded imports.
"""


import_code = r'''
from blendscript.compiler.val   import *
from blendscript.compiler.types import *
from blendscript.parsers.bmesh  import *
'''.strip()


exec(import_code, globals())


print(f"""
# BlendScript Python shell
{import_code}
""")
