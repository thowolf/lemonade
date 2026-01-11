from scripts.benchmarks.continue_testing.test_runner import run_interactive
inputs = iter(['', 'y', '100', '', 'y', '100', '', 'y', '100'])
import builtins
builtins.input = lambda prompt='': next(inputs)
res = run_interactive('m1', interactions=3, config_dir=None, results_dir='C:\\Temp', verbose=True, output_format='all')
print('RES:', repr(res))
