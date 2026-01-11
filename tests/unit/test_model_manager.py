import os
from scripts.benchmarks.continue_testing.model_manager import ConfigLoader, ModelManager


def test_config_loader_loads_models_and_scenarios():
    cfg_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "benchmarks", "continue-testing", "config")
    cfg_dir = os.path.normpath(cfg_dir)
    loader = ConfigLoader(cfg_dir)
    models = loader.load_models()
    scenarios = loader.load_scenarios()
    assert isinstance(models, list) and len(models) >= 1
    assert isinstance(scenarios, list) and len(scenarios) >= 1


def test_model_manager_initialization():
    cfg_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "benchmarks", "continue-testing", "config")
    cfg_dir = os.path.normpath(cfg_dir)
    manager = ModelManager(cfg_dir)
    assert hasattr(manager, '_models')
    assert isinstance(manager._models, dict)


def test_model_manager_get_model_by_name():
    cfg_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "benchmarks", "continue-testing", "config")
    cfg_dir = os.path.normpath(cfg_dir)
    manager = ModelManager(cfg_dir)
    
    # Test with existing model (assuming models.yaml has at least one model)
    models = manager.load_model_config()
    if models:
        first_model_name = list(models.keys())[0]
        model = manager.get_model_by_name(first_model_name)
        assert model is not None
        assert model['name'] == first_model_name
    
    # Test with non-existing model
    model = manager.get_model_by_name("non-existing-model")
    assert model is None


def test_model_manager_load_model_config():
    cfg_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "benchmarks", "continue-testing", "config")
    cfg_dir = os.path.normpath(cfg_dir)
    manager = ModelManager(cfg_dir)
    
    config = manager.load_model_config()
    assert isinstance(config, dict)
    assert len(config) >= 1  # Should have at least one model
    
    # Check that each model has required fields
    for name, model in config.items():
        assert 'name' in model
        assert 'source' in model
        assert 'quantization' in model
        assert model['name'] == name


def test_config_loader_validate_config():
    cfg_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "benchmarks", "continue-testing", "config")
    cfg_dir = os.path.normpath(cfg_dir)
    loader = ConfigLoader(cfg_dir)
    
    # Test validation for models
    try:
        result = loader.validate_config("models")
        assert result is True
    except Exception as e:
        # If yamale is not installed, it should raise RuntimeError
        assert "Yamale" in str(e) or "yamale" in str(e)
