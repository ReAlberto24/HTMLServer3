import sys
import os
from plugin_manager import Manager
sys.path.append(os.path.join(os.getcwd(), 'plugins', 'test'))

manager = Manager()


@manager.endpoint('/hello-world')
def x(args: dict[str, str], **kwargs) -> (str, int):
    return args.get('text'), 200


# @manager.wrap('on-load')
# def on_load():
#     print('Hello, World!')
