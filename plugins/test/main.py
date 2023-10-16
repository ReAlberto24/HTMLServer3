import sys
import os
from plugin_manager import Manager
sys.path.append(os.path.join(os.getcwd(), 'plugins', 'test'))

manager = Manager()


@manager.wrap('on-load')
def foo(name: str = None):
    print(f'Hello, {'World' if name is None else name}!')
