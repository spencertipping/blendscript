import ast
import sys


def parsed_list_limit(n):
  try:
    eval('[' * n + ']' * n)
    return parsed_list_limit(n + 1)
  except:
    return n - 1


def ast_list_limit(n):
  print(f'ast: trying {n}')

  l = ast.List([], ast.Load())
  for i in range(n - 1):
    l = ast.List([l], ast.Load())
  ast.fix_missing_locations(l)
  try:
    eval(compile(ast.Expression(l), 'ast_test', 'eval'))
    return ast_list_limit(int(n * 1.1) + 1)
  except Exception as e:
    print(e)
    return n // 2


sys.setrecursionlimit(100000)

print(f'parsed list limit = {parsed_list_limit(1)}')
print(f'ast    list limit = {ast_list_limit(1)}')
