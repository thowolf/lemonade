from scripts.benchmarks.continue_testing.test_runner import _input_yes_no, _input_float_optional


def test_input_yes_no_accepts_yes(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': 'y')
    assert _input_yes_no('prompt') is True


def test_input_yes_no_retries_then_default(monkeypatch):
    inputs = iter(['maybe', '', 'n'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(inputs))
    assert _input_yes_no('prompt') is False


def test_input_float_optional_blank(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': '')
    assert _input_float_optional('prompt') is None


def test_input_float_optional_value(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': '123.45')
    assert abs(_input_float_optional('prompt') - 123.45) < 1e-6
