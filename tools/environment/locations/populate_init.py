import os, sys
if __name__ == "__main__":

    path = os.path.dirname(os.path.abspath(__file__))
    ignore = ('populate_init.py', '__init__.py')
    files = [f[:-3] for f in os.listdir(path) if f.endswith('.py') and f not in ignore]
    with open(f'{path}/__init__.py', 'w+') as f:
        for py in files:
            f.write(f"from .{py} import *\n")