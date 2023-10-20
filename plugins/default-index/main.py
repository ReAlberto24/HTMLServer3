import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'plugins', 'test'))
from plugin_manager import Manager
from flask import make_response, redirect, Request
import re


manager = Manager()


@manager.endpoint('/login')
def x(**kwargs) -> (..., int):
    response = make_response(
        redirect('/')
    )
    response.set_cookie('bruh', '1')
    return response, 302


@manager.endpoint('/hi.plugin')
def x(**kwargs) -> (..., int):
    response = ''
    for i in range(10):
        response += f'<p>{i}</p>'
    return response, 200


@manager.wrap('on-load')
def on_load():
    print('Plugin Loaded!')


# def is_mobile_user_agent(user_agent_string):
#     if re.search(r'mobile|android|ios|iphone|ipad', user_agent_string, re.I):
#         return True
#     else:
#         return False


# @manager.wrap('on-request')
# def on_load(request: Request):
#     if is_mobile_user_agent(request.user_agent.string):
#         print('Request from mobile')
#     else:
#         print('Request from desktop')
