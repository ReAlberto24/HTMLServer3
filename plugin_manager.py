class ManagerError(Exception):
    def __init__(self, _type: str, message: str):
        self._type = _type
        self.message = message

    def __str__(self):
        return f'ManagerError<{self._type}>: {self.message}'


class Manager:
    def __init__(self):
        self.functions = {}

    def wrap(self, id_: str):
        def decorator(func):
            self.functions[id_] = func

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def call(self, id_: str, *args, **kwargs):
        if self.functions.get(id_) is not None:
            return self.functions[id_](*args, **kwargs)
        else:
            raise ManagerError('FunctionNotFound', 'Cannot find the requested id_')
