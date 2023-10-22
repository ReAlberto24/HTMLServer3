
# Plugin Loader V1.0
#

import os
from dataclasses import dataclass
from types import ModuleType
from typing import Any
from server_funcs import flatten_dict
from yaml import safe_load
import io
import sys
import importlib.util
import contextlib
from colors import FC, OPS
from plugin_manager import Manager, ManagerError


def check_requirements_from_dict(data: dict) -> bool:
    required_attrs = ('plugin.name', 'plugin.version', 'plugin.main-file',
                      'plugin.id', 'loader.required-version', 'loader.preferred-version')
    for key in flatten_dict(data).keys():
        if not (key in required_attrs):
            return False
    flatten_data = flatten_dict(data)
    for attr in required_attrs:
        if flatten_data.get(attr) is None:
            return False
    return True


@dataclass
class PluginConfiguration:
    name: str
    version: float
    main_file: str
    id_: str
    loader_required: float
    loader_preferred: float

    def from_dict(self, data: dict):
        # if check_requirements_from_dict(data=data):
        flatten_data = flatten_dict(data)
        self.name = flatten_data.get('plugin.name')
        self.version = flatten_data.get('plugin.version')
        self.main_file = flatten_data.get('plugin.main-file')
        self.id_ = flatten_data.get('plugin.id')
        self.loader_required = flatten_data.get('loader.required-version')
        self.loader_preferred = flatten_data.get('loader.preferred-version')


class PrefixedStringIO(io.StringIO):
    def __init__(self, prefix, *args, **kwargs):
        self.prefix = prefix
        self.added = False
        super().__init__(*args, **kwargs)

    def write(self, s):
        if not self.added:
            sys.__stdout__.write(self.prefix + s)
            self.added = True
        else:
            sys.__stdout__.write(s)
        if '\n' in s:
            self.added = False


class Plugin:
    def __init__(self,
                 configuration: PluginConfiguration,
                 stdout_buffer: PrefixedStringIO):
        self.configuration: PluginConfiguration = configuration
        self.main_file: str = configuration.main_file
        self.stdout_buffer: PrefixedStringIO = stdout_buffer

        self.injected_attrs = []
        self.module: ModuleType = None
        self.manager: Manager = None

    def inject_attr(self, attr: Any, attr_name: str) -> None:
        self.injected_attrs.append((attr, attr_name))

    def init(self) -> None:
        name = self.main_file.split(os.sep)[-1].split('.')[0]
        spec = importlib.util.spec_from_file_location(name, self.main_file)
        module = importlib.util.module_from_spec(spec)
        for attr, name in self.injected_attrs:
            setattr(module, name, attr)
        with contextlib.redirect_stdout(self.stdout_buffer):
            spec.loader.exec_module(module)
        self.module = module

    def load_manager(self) -> None:
        self.manager = self.module.manager


class PluginError(Exception):
    def __init__(self, _type: str, message: str):
        self._type = _type
        self.message = message

    def __str__(self):
        return f'PluginError<{self._type}>: {self.message}'


class LoaderState:
    base: int = 0
    load_plugins: int = 1
    init_plugins: int = 2
    loaded_managers: int = 3


class Loader:
    def __init__(self,
                 plugin_directory: str = 'plugins',
                 raise_on_error: bool = False):
        self.directory = plugin_directory
        self.plugins: list[Plugin] = []
        self.plugin_loaded = LoaderState.base
        self.roe = raise_on_error

    def load_plugins(self):
        for plugin in os.listdir(self.directory):
            plugin_path = os.path.join(self.directory, plugin)
            if not os.path.exists(os.path.join(plugin_path, 'plugin.yml')):
                if self.roe:
                    raise PluginError('Loader', f'Plugin "{plugin}" doesn\'t contain a "plugin.yml" file')
                print(str(PluginError('Loader', f'Plugin "{plugin}" doesn\'t contain a "plugin.yml" file')))
                continue
            with open(os.path.join(plugin_path, 'plugin.yml'), 'r') as _f_plugin_configuration:
                plugin_configuration = safe_load(_f_plugin_configuration)
            if check_requirements_from_dict(data=plugin_configuration):
                plugin_conf = PluginConfiguration(
                    name=None,
                    version=None,
                    main_file=None,
                    id_=None,
                    loader_required=None,
                    loader_preferred=None
                )
                plugin_conf.from_dict(data=plugin_configuration)
                # Fix for the damn main file
                plugin_conf.main_file = os.path.join(self.directory, plugin, plugin_conf.main_file)
            else:
                if self.roe:
                    raise PluginError('Loader', f'Plugin "{plugin}" configuration isn\'t complete')
                print(str(PluginError('Loader', f'Plugin "{plugin}" configuration isn\'t complete')))
                continue

            plg: Plugin = Plugin(
                configuration=plugin_conf,
                stdout_buffer=PrefixedStringIO(f'Plugin<{FC.LIGHT_MAGENTA}{plugin_conf.id_}{OPS.RESET}> ')
            )

            self.plugins.append(plg)
        self.plugin_loaded = LoaderState.load_plugins

    def init_plugins(self):
        if self.plugin_loaded < LoaderState.load_plugins:
            if self.roe:
                raise PluginError('Loader', f'Use .load_plugins() before')
            print(str(PluginError('Loader', f'Use .load_plugins() before')))
            return
        for plugin in self.plugins:
            plugin.init()
        self.plugin_loaded = LoaderState.init_plugins

    def load_managers(self):
        if self.plugin_loaded < LoaderState.init_plugins:
            if self.roe:
                raise PluginError('Loader', f'Use .init_plugins() before')
            print(str(PluginError('Loader', f'Use .init_plugins() before')))
            return
        for plugin in self.plugins:
            plugin.load_manager()
            # Another ID
            #   if plugin.manager.functions.get('on-manager-load') is not None:
            #       plugin.manager._call_id('on-manager-load')
        self.plugin_loaded = LoaderState.loaded_managers

    def call_id(self, id_, *args, **kwargs):
        if self.plugin_loaded < LoaderState.loaded_managers:
            if self.roe:
                raise PluginError('Loader', f'Use .init_plugins() before')
            print(str(PluginError('Loader', f'Use .init_plugins() before')))
            return
        for plugin in self.plugins:
            try:
                with contextlib.redirect_stdout(plugin.stdout_buffer):
                    plugin.manager._call_id(id_, *args, **kwargs)
            except ManagerError as e:
                # if e._type == 'FunctionNotFound':
                #     pass
                continue

    def check_endpoint(self, endpoint) -> bool:
        if self.plugin_loaded < LoaderState.loaded_managers:
            if self.roe:
                raise PluginError('Loader', f'Use .init_plugins() before')
            print(str(PluginError('Loader', f'Use .init_plugins() before')))
            return
        for plugin in self.plugins:
            if endpoint in plugin.manager.endpoints:
                return True
        return False

    def call_endpoint(self, endpoint, *args, **kwargs) -> (str, int):
        if self.plugin_loaded < LoaderState.loaded_managers:
            if self.roe:
                raise PluginError('Loader', f'Use .init_plugins() before')
            print(str(PluginError('Loader', f'Use .init_plugins() before')))
            return
        for plugin in self.plugins:
            try:
                with contextlib.redirect_stdout(plugin.stdout_buffer):
                    return plugin.manager._call_endpoint(endpoint, *args, **kwargs)
            except ManagerError as e:
                # if e._type == 'FunctionNotFound':
                #     pass
                continue
