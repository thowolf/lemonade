# Configuration Contracts

This directory contains JSON Schema definitions for test configuration files and output formats.

## Files

- **models.schema.json** - Schema for `config/models.yaml` model configurations
- **test_scenarios.schema.json** - Schema for `config/test_scenarios.yaml` test scenarios
- **test_run.schema.json** - Schema for test run output files
- **compatibility_result.schema.json** - Schema for compatibility matrix reports

## Usage

These schemas enable:
1. Configuration validation before running tests
2. IDE autocomplete when editing YAML configs
3. Automated validation in CI/CD pipelines
4. Contract testing for output format stability

## Validation Example

```python
import jsonschema
import yaml
import json

# Load schema
with open('contracts/models.schema.json') as f:
    schema = json.load(f)

# Load config
with open('config/models.yaml') as f:
    config = yaml.safe_load(f)

# Validate
jsonschema.validate(instance=config, schema=schema)
```
