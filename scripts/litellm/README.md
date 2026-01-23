# LiteLLM Proxy Server

LiteLLM Proxy provides a unified API interface for managing and routing requests to multiple LLM backends.

## Features

- **Multi-backend support**: Route to OpenAI, Anthropic, Local models, etc.
- **Model aliasing**: Map multiple model providers to simple aliases
- **API key management**: Centralized key management for different backends
- **Caching**: Built-in request caching for common queries
- **Load balancing**: Distribute requests across multiple endpoints
- **Comprehensive logging**: Track all API calls and performance metrics

## Quick Start

### Start LiteLLM Proxy

```bash
# Default (port 8090)
.\start-litellm.bat

# Or with PowerShell
.\start-litellm.ps1 -Port 8090

# Force restart if already running
.\start-litellm.ps1 -Force
```

### Configuration

Create or edit `config/litellm_config.yaml`:

```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: $OPENAI_API_KEY
      
  - model_name: claude-3
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: $ANTHROPIC_API_KEY

general_settings:
  log_file: "litellm_logs.log"
  cache:
    type: redis
    host: localhost
```

## API Usage

### List Models

```bash
curl http://localhost:8090/models
```

### Make a Request

```bash
curl http://localhost:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Integration with Lemonade

LiteLLM can be used as a backend router for Lemonade Server to provide:
- Consistent API across different model providers
- Centralized model management
- Advanced routing and load balancing

## Documentation

- [LiteLLM Official Docs](https://docs.litellm.ai/)
- [Configuration Guide](https://docs.litellm.ai/docs/proxy/configs)
- [API Reference](https://docs.litellm.ai/docs/proxy/user_config)

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
.\start-litellm.ps1 -Port 8091
```

### Configuration Not Loading

- Check `config/litellm_config.yaml` syntax
- Verify all required environment variables are set
- Check logs in `litellm_logs.log`

### API Key Issues

Set environment variables or use config file:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

## Support

For issues or questions:
1. Check [LiteLLM documentation](https://docs.litellm.ai/)
2. Review logs in `litellm_logs.log`
3. Open an issue on the project repository
