# Shim loader that imports the implementation from the filesystem path with hyphen
# This allows `import scripts.benchmarks.continue_testing.metrics_collector` to work
import importlib.util
import os
import sys
from importlib.machinery import SourceFileLoader

_this_dir = os.path.dirname(__file__)
_impl_path = os.path.normpath(os.path.join(_this_dir, '..', 'continue-testing', 'metrics_collector.py'))

if os.path.exists(_impl_path):
    loader = SourceFileLoader('continue_testing_impl.metrics_collector', _impl_path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    # Ensure module is available in sys.modules so dataclasses and imports work correctly
    sys.modules[loader.name] = module
    loader.exec_module(module)
    # Export module symbols into this shim module's globals
    globals().update({k: v for k, v in module.__dict__.items() if not k.startswith('__')})
else:
    raise ImportError(f"Implementation module not found: {_impl_path}")
