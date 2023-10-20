import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'plugins', 'default-index'))
from plugin_manager import Manager
from random import choices, randint
from string import hexdigits


manager = Manager()


@manager.wrap('on-load')
def on_load():
    print('Plugin Loaded!')


@manager.endpoint('/index.plugin')
def endpoint(**kwargs) -> (..., int):
    if randint(0, 1_000_000_000) == 0:
        contents = '<span>Made By ReAlberto24</span>'
        print('Special Text')
    else:
        contents = (f'<span style="color: #{''.join(choices(hexdigits.lower(), k=6))}">'
                    f'{''.join(choices(hexdigits.lower(), k=24))}'
                    f'</span>')
    return contents, 200
