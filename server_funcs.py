import requests
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


def is_server_up(server_url, timeout=3, max_retries=2):
    for _ in range(max_retries):
        try:
            response = requests.get(server_url, timeout=timeout)
            if response.status_code == 200:
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
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


def is_default_type(variable):
    default_types = (int, float, complex, list, tuple, range, dict, set, frozenset, bool, bytes, bytearray, memoryview, type(None))
    return any(isinstance(variable, t) for t in default_types)
