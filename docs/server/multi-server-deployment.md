# Multi-Server Deployment Guide

## Overview

Lemonade Server supports running multiple server instances simultaneously on different ports. This allows you to:

- Run different models in parallel (e.g., chat, code, fast-response models)
- Implement load balancing across multiple instances
- Separate development, staging, and production environments
- Test model comparisons side-by-side

## Prerequisites

- Lemonade Server installed ([Installation Guide](../install_options.html))
- Models downloaded via `lemonade-server pull <model-name>`
- PowerShell 5.1+ (Windows) or Bash 4.0+ (Linux)
- `jq` for JSON parsing (Linux only): `sudo apt-get install jq`

## Quick Start

### 1. Navigate to Scripts Directory

```bash
cd scripts/multi-server
```

### 2. Configure Your Servers

Edit `config/example-config.json`:

```json
{
  "servers": [
    {
      "name": "llama-server",
      "port": 8000,
      "model": "Llama-3.2-3B-Instruct",
      "llamacpp_backend": "vulkan",
      "ctx_size": 4096,
      "log_level": "info"
    },
    {
      "name": "qwen-server",
      "port": 8001,
      "model": "Qwen3-0.6B-GGUF",
      "llamacpp_backend": "vulkan",
      "ctx_size": 2048,
      "log_level": "info"
    }
  ]
}
```

### 3. Start All Servers

**Windows:**
```powershell
.\start-multi-server.ps1
```

**Linux/macOS:**
```bash
./start-multi-server.sh
```

### 4. Verify Status

**Windows:**
```powershell
.\status-multi-server.ps1
```

**Linux/macOS:**
```bash
./status-multi-server.sh
```

### 5. Test Endpoints

```bash
# Test server on port 8000
curl http://localhost:8000/api/v1/health

# Test server on port 8001
curl http://localhost:8001/api/v1/health
```

## Management Scripts

All scripts are located in `scripts/multi-server/`:

| Script | Purpose |
|--------|---------|
| `validate-config` | Validate configuration and check ports |
| `start-multi-server` | Start all configured servers |
| `stop-multi-server` | Stop all running servers |
| `restart-multi-server` | Restart servers (stop + start) |
| `status-multi-server` | Check server status and health |

### Detailed Usage

#### Validate Configuration

Checks configuration file syntax and port availability before starting servers.

**Windows:**
```powershell
.\validate-config.ps1                          # Default config
.\validate-config.ps1 config\prod.json         # Custom config
.\validate-config.ps1 -SkipPortCheck           # Skip port checks
```

**Linux:**
```bash
./validate-config.sh                            # Default config
./validate-config.sh config/prod.json           # Custom config
./validate-config.sh --skip-port-check          # Skip port checks
```

#### Start Servers

Starts all servers defined in configuration file as background processes.

**Windows:**
```powershell
.\start-multi-server.ps1                       # Default config
.\start-multi-server.ps1 config\prod.json      # Custom config
.\start-multi-server.ps1 -Force                # Force start (skip port checks)
```

**Linux:**
```bash
./start-multi-server.sh                         # Default config
./start-multi-server.sh config/prod.json        # Custom config
./start-multi-server.sh --force                 # Force start
```

**Output Files:**
- PIDs: `pids/server-{port}.pid`
- Logs: `logs/server-{port}.log`

#### Stop Servers

Gracefully stops all running servers.

**Windows:**
```powershell
.\stop-multi-server.ps1                        # Stop all
.\stop-multi-server.ps1 -Port 8000             # Stop specific port
.\stop-multi-server.ps1 -Force                 # Force kill
```

**Linux:**
```bash
./stop-multi-server.sh                          # Stop all
./stop-multi-server.sh --port 8000              # Stop specific port
./stop-multi-server.sh --force                  # Force kill
```

#### Restart Servers

Stops and restarts all servers (useful after config changes).

**Windows:**
```powershell
.\restart-multi-server.ps1                     # Restart all
.\restart-multi-server.ps1 -Port 8000          # Restart specific port
```

**Linux:**
```bash
./restart-multi-server.sh                       # Restart all
./restart-multi-server.sh --port 8000           # Restart specific port
```

#### Check Status

Displays status of all configured servers including health checks.

**Windows:**
```powershell
.\status-multi-server.ps1                      # Basic status
.\status-multi-server.ps1 -Verbose             # Show loaded models
.\status-multi-server.ps1 -Port 8000           # Check specific port
```

**Linux:**
```bash
./status-multi-server.sh                        # Basic status
./status-multi-server.sh --verbose              # Show loaded models
./status-multi-server.sh --port 8000            # Check specific port
```

## Configuration Reference

See [scripts/multi-server/README.md](../../scripts/multi-server/README.md) for complete configuration schema.

### Required Fields

- `name`: Unique server identifier
- `port`: Port number (1024-65535)
- `model`: Model name (must be installed)

### Optional Fields

- `llamacpp_backend`: `vulkan` (default), `rocm`, or `cpu`
- `ctx_size`: Context size (default: 4096)
- `log_level`: `info` (default), `debug`, `warning`, `error`
- `host`: Bind address (default: `localhost`)
- `max_loaded_models`: Max models per type (default: `1 1 1 1`)
- `extra_args`: Additional CLI arguments

## Common Use Cases

### Development: Test Multiple Models

```json
{
  "servers": [
    {
      "name": "dev-llama",
      "port": 8000,
      "model": "Llama-3.2-3B-Instruct",
      "log_level": "debug"
    },
    {
      "name": "dev-qwen",
      "port": 8001,
      "model": "Qwen3-0.6B-GGUF",
      "log_level": "debug"
    }
  ]
}
```

### Production: Specialized Models

```json
{
  "servers": [
    {
      "name": "chat-production",
      "port": 8000,
      "model": "Llama-3.2-3B-Instruct",
      "ctx_size": 8192,
      "log_level": "warning"
    },
    {
      "name": "code-production",
      "port": 8001,
      "model": "CodeLlama-7B",
      "ctx_size": 4096,
      "log_level": "warning"
    }
  ]
}
```

### Load Balancing

Use a reverse proxy (nginx, Caddy) to distribute requests:

```nginx
upstream lemonade_backends {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://lemonade_backends;
    }
}
```

## Docker Deployment

For containerized deployment, see `scripts/multi-server/docker-compose.yml`.

**Start with Docker Compose:**
```bash
cd scripts/multi-server
docker-compose up -d
```

**Check logs:**
```bash
docker-compose logs -f llama-server
docker-compose logs -f qwen-server
```

**Stop containers:**
```bash
docker-compose down
```

## Troubleshooting

### Port Already in Use

**Error:**
```
❌ Port 8000 is already in use
```

**Solution:**
1. Check what's using the port:
   - Windows: `netstat -ano | findstr :8000`
   - Linux: `lsof -i :8000`
2. Stop the conflicting process
3. Or change port in configuration

### Server Won't Start

**Error:**
```
⚠️  Server not running (PID: 12345)
```

**Solution:**
1. Check logs: `logs/server-{port}.log`
2. Verify model installed: `lemonade-server pull <model-name>`
3. Check available memory: Run fewer servers or use smaller models

### Health Check Fails

**Error:**
```
❌ Unhealthy - Cannot reach health endpoint
```

**Solution:**
1. Server may still be starting (wait 10-30 seconds)
2. Check if process is running: `.\status-multi-server.ps1`
3. Inspect logs for errors

### Out of Memory

**Error:**
```
Server crashed - insufficient memory
```

**Solution:**
1. Reduce `ctx_size` in configuration
2. Run fewer servers simultaneously
3. Use smaller models
4. Monitor memory usage: `.\status-multi-server.ps1 -Verbose`

## Performance Considerations

### Memory Requirements

Estimate memory per server:
- Small model (0.6B-3B): 2-6 GB VRAM + 2 GB system RAM
- Medium model (7B-13B): 6-12 GB VRAM + 4 GB system RAM
- Large model (30B+): 16+ GB VRAM + 8+ GB system RAM

**Example System (128GB RAM, 96GB VRAM):**
- 3x Large models (3 × 16GB VRAM = 48GB)
- 4x Medium models (4 × 8GB VRAM = 32GB)
- 10x Small models (10 × 4GB VRAM = 40GB)

### Port Assignment

Use consistent port ranges:
- Development: 8000-8009
- Staging: 8010-8019
- Production: 8020-8029

### Log Management

Logs grow over time. Rotate regularly:

**Windows (PowerShell):**
```powershell
# Archive old logs
Compress-Archive -Path logs\*.log -DestinationPath logs\archive-$(Get-Date -Format 'yyyyMMdd').zip
Remove-Item logs\*.log
```

**Linux (Bash):**
```bash
# Archive old logs
tar -czf logs/archive-$(date +%Y%m%d).tar.gz logs/*.log
rm logs/*.log
```

## API Reference

Each server instance exposes the full Lemonade Server API:

- `GET /api/v1/health` - Health check
- `POST /api/v1/load` - Load model
- `POST /api/v1/unload` - Unload model
- `GET /api/v1/models` - List loaded models
- `POST /api/v1/chat/completions` - Chat (OpenAI-compatible)
- `POST /api/v1/completions` - Completions (OpenAI-compatible)

Full API documentation: [Lemonade Server API](lemonade_api.md)

## Related Documentation

- [Installation Guide](../install_options.html)
- [Server CLI Reference](server/lemonade-server-cli.md)
- [API Documentation](lemonade_api.md)
- [Multi-Server Scripts README](../../scripts/multi-server/README.md)

## Support

- [FAQ](faq.md)
- [GitHub Issues](https://github.com/lemonade-server/lemonade/issues)
- Specification: `specs/005-multi-llm-execution/`
