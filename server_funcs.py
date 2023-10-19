import socket
import os


def flatten_dict(input_dict, parent_key='', separator='.'):
    flattened_dict = {}
    for key, value in input_dict.items():
        new_key = f'{parent_key}{separator}{key}' if parent_key else key

        if isinstance(value, dict):
            flattened_dict.update(flatten_dict(value, new_key, separator))
        else:
            flattened_dict[new_key] = value

    return flattened_dict


def create_basic_socket_server(server_port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(('0.0.0.0', server_port))
        server_sock.listen(5)
        client_sock, _ = server_sock.accept()
        client_sock.send(b'ping')
        if client_sock.recv(1024) == b'pong':
            client_sock.close()
            return


def create_basic_socket_client(server_addr: str, server_port: int):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
            client_sock.connect((server_addr, server_port))
            if client_sock.recv(1024) == b'ping':
                client_sock.send(b'pong')
                client_sock.close()
                return True
    except Exception:
        return False


def resolve_directory_path(directory_path):
    normalized_path = os.path.normpath(directory_path)
    resolved_path = normalized_path.replace('..', '')
    resolved_path = resolved_path.replace('//', '/')
    return resolved_path


def is_in_directory(root, path):
    current_directory = os.path.abspath(os.getcwd())
    target_path = os.path.abspath(path)
    return target_path.startswith(current_directory)


def check_error_code(return_code, error_codes_handled, _request, _get_request_error, abort):
    if return_code in error_codes_handled:
        if _request.method == 'GET' and _get_request_error in ('always', 'no-header' if not _request.headers.get('No-Error-Handler') else None):
            return '', 404
        abort(404)
