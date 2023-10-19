# General
from colors import OPS, FC
import os
import sys

# Config
import argparse
from yaml import safe_load
from server_classes import Config, Utils
from server_funcs import (flatten_dict, create_basic_socket_client, create_basic_socket_server,
                          resolve_directory_path, is_in_directory, check_error_code)

# Web Server
from flask import Flask, send_file, abort, request
import waitress
import socket
import http.client
from threading import Thread
import subprocess
import json

# Plugin Stuff
from plugin_loader import Loader

app = Flask(__name__)
root_directory = ''
get_request_error = ''
loader = Loader(
    plugin_directory=os.path.join(os.getcwd(), 'plugins'),
    raise_on_error=False
)
error_codes_handled = []


@app.route('/', methods=['GET'])
def flask_index() -> (str, int):
    if os.path.exists(os.path.join(root_directory, 'index.html')):
        # File
        print(f'{FC.LIGHT_RED} {request.method} - / - 200')
        return send_file(os.path.join(root_directory, 'index.html')), 200
    print(f'{FC.DARK_RED} {request.method} - / - 404')
    abort(404)


@app.route('/<path:file>', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'])
def flask_file(file: str) -> (str, int):
    # Plugin Implementation
    if loader.check_endpoint(f'/{file}'):
        data, _return_code = loader.call_endpoint(f'/{file}',
                                                  args=request.args if request.method == 'GET' else None,
                                                  form=request.form if request.method == 'POST' else None,
                                                  json=request.json if request.method == 'POST' else None)
        print(f'{FC.DARK_GREEN} {request.method} - /{file} - {_return_code}{OPS.RESET}')
        if _return_code in error_codes_handled:
            if request.method == 'GET' and get_request_error == 'always':
                abort(404)
            elif request.method == 'GET' and get_request_error == 'no-header':
                if request.headers.get('No-Error-Handler') is not None:
                    return '', 404
                abort(404)
            return '', 404
        return str(data), _return_code
    f = resolve_directory_path(os.path.join(root_directory, *file.split('/')))
    if os.path.exists(f) and is_in_directory(root_directory, f):
        if os.path.isdir(f):
            if os.path.exists(os.path.join(f, 'index.html')):
                # File
                print(f'{FC.LIGHT_RED} {request.method} - /{file} - 200{OPS.RESET}')
                return send_file(os.path.join(f, 'index.html')), 200
            if request.method == 'GET' and get_request_error == 'always':
                print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
                abort(404)
            elif request.method == 'GET' and get_request_error == 'no-header':
                if request.headers.get('No-Error-Handler') is not None:
                    print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
                    return '', 404
                print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
                abort(404)
            print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
            return '', 404
        # File
        extension = f.rsplit('.', 1)[1]
        if extension in ('py', ):
            match request.method:
                case 'GET':
                    process = subprocess.run([sys.executable, f,
                                              json.dumps(request.args), json.dumps(request.cookies)],
                                             stderr=subprocess.STDOUT,
                                             stdout=subprocess.PIPE,
                                             stdin=subprocess.DEVNULL,
                                             cwd=os.path.dirname(f))
                    data = json.loads(process.stdout)
                    contents, return_code = data[0], data[1]
                    print(f'{FC.LIGHT_MAGENTA} {request.method} - /{file} - {return_code}{OPS.RESET}')
                    try:
                        # Handle error
                        if data[2]:
                            abort(return_code)
                    except IndexError:
                        pass
                    return contents, return_code
        print(f'{FC.LIGHT_RED} {request.method} - /{file} - 200{OPS.RESET}')
        return send_file(f), 200
    if request.method == 'GET' and get_request_error == 'always':
        print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
        abort(404)
    elif request.method == 'GET' and get_request_error == 'no-header':
        if request.headers.get('No-Error-Handler') is not None:
            print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
            return '', 404
        print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
        abort(404)
    print(f'{FC.DARK_RED} {request.method} - /{file} - 404{OPS.RESET}')
    return '', 404

# @app.errorhandler(404)
# def flask_error_404(err):
#     return send_file(os.path.join(root_directory, '404.html')), 200

print('Preloading Error Handlers')
for handler_file in os.listdir('error_handlers'):
    handler_path = os.path.join(os.getcwd(), 'error_handlers', handler_file)

    with open(handler_path, 'r') as _f_handler:
        handler_data = safe_load(_f_handler)

    error_code = handler_data.get('error-code')
    redirect_to = handler_data.get('redirect-to')
    return_value = handler_data.get('return')
    return_code = handler_data.get('return-code')


    def create_error_handler(_redirect_to, _return_value, _return_code):
        def error_handler(err):
            if _return_value is None:
                return send_file(os.path.join(root_directory, _redirect_to))
            else:
                return _return_value, _return_code

        return error_handler


    print(f'Adding error handler for: {FC.DARK_CYAN}{error_code}{OPS.RESET}')
    # Plugin Fix
    error_codes_handled.append(error_code)
    app.errorhandler(error_code)(create_error_handler(redirect_to, return_value, return_code))

print('Loading plugins')
loader.load_plugins()
loader.init_plugins()
loader.load_managers()
print('Plugins loaded, running on-load')
loader.call_id('on-load')

if __name__ == '__main__':
    print(f'Loading {FC.LIGHT_GREEN}conf.yml{OPS.RESET}')
    with open(os.path.join(os.getcwd(), 'conf.yml'), 'r') as _f_conf:
        conf = safe_load(_f_conf)

    root_directory = os.path.join(*str(conf['server-default']['root-directory']).replace(
        '$(cwd)', os.getcwd()
    ).split('/'))
    get_request_error = conf['GET-request-error']

    parser = argparse.ArgumentParser(
        description='details',
        usage='Use "%(prog)s --help" for more information',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('--port',
                        help=f'Specify the port to use (1 - 65535) - Default: {conf['server-default']
                                                                                   ['port']}',
                        default=None,
                        type=int
                        )
    parser.add_argument('--threads',
                        help=f'Set how many threads the server can use - Default: {conf['server-default']
                                                                                       ['wsgi-threads']}',
                        default=None,
                        type=int
                        )

    parser.add_argument('-v', '--verbose',
                        help=f'Enable detailed informations - Default: {conf['server-default']
                                                                            ['verbose']}',
                        default=conf['server-default']['verbose'],
                        action='store_true'
                        )

    print('Parsing arguments')
    args = parser.parse_args()
    full_conf = Config(port=conf['server-default']['port'],
                       threads=conf['server-default']['wsgi-threads'],
                       verbose=conf['server-default']['verbose'])

    print('Finalising configuration')
    if (args.port is not None) and (1 <= args.port):
        full_conf.port = args.port

    if (args.threads is not None) and (1 <= args.threads):
        full_conf.threads = args.threads

    if args.verbose is not None:
        full_conf.verbose = args.verbose

    util = Utils(config=full_conf)

    # Verbose printing in not enough optimizations
    if full_conf.verbose:
        print('File configuration:')
        for key, value in flatten_dict(conf).items():
            print(f'{FC.LIGHT_YELLOW}  {key}{OPS.RESET}: {FC.LIGHT_CYAN}{value}{OPS.RESET}')

        print('Configuration:')
        for key, value in full_conf.to_dict().items():
            print(f'{FC.LIGHT_YELLOW}  {key}{OPS.RESET}: {FC.LIGHT_CYAN}{value}{OPS.RESET}')

    # Gets Nat and Public address
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        nat_addr = s.getsockname()[0]

    conn = http.client.HTTPSConnection('ipv4.icanhazip.com')
    conn.request('GET', '/')
    public_add = conn.getresponse().read().decode('utf-8').strip()
    del conn

    # # Check for public connections
    # util.verbose_print('Checking public ip connection')
    # # Server Thread
    # threading.Thread(target=create_basic_socket_server, args=(full_conf.port, ), daemon=True).start()
    # # Client
    # if create_basic_socket_client(public_add, full_conf.port):
    #     public_enabled = True
    # else:
    #     print(f'{FC.LIGHT_RED}Public address not reachable, '
    #           f'add firewall rule or enable port forwarding on the router{OPS.RESET}')
    #     public_enabled = False

    # Starts the server
    print('Starting WebServer, use CTRL+C to exit')
    print(f'Connect to the server using this links:\n'
          f'  {FC.LIGHT_BLUE}Private{OPS.RESET}: '
          f'http://127.0.0.1{'' if full_conf.port == 80 else f':{full_conf.port}'}/\n'
          
          f'  {FC.LIGHT_BLUE}Local{OPS.RESET}:   '
          f'http://{nat_addr}{'' if full_conf.port == 80 else f':{full_conf.port}'}/\n'
          
          f'  {FC.LIGHT_BLUE}Public{OPS.RESET}:  '
          f'http://{public_add}{'' if full_conf.port == 80 else f':{full_conf.port}'}/')
    waitress.serve(app, host='0.0.0.0', port=full_conf.port, threads=full_conf.threads)

    print('Exiting the server')
