# Shim loader that imports the implementation from the filesystem path with hyphen
import importlib.util
import os
import sys
from importlib.machinery import SourceFileLoader

_this_dir = os.path.dirname(__file__)
_impl_path = os.path.normpath(os.path.join(_this_dir, '..', 'continue-testing', 'report_generator.py'))

if os.path.exists(_impl_path):
    loader = SourceFileLoader('continue_testing_impl.report_generator', _impl_path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    globals().update({k: v for k, v in module.__dict__.items() if not k.startswith('__')})
else:
    raise ImportError(f"Implementation module not found: {_impl_path}")
