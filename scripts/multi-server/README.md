# Lemonade Multi-Server Management Scripts

Orchestrate multiple Lemonade Server instances running simultaneously on different ports using Docker Compose or native scripts.

## Docker Compose Setup (Recommended)

This approach uses Docker containers to run multiple server instances, avoiding the single-instance lock limitation by isolating each server in its own container.

### Prerequisites

- Docker and Docker Compose installed
- CMake 3.28.4 or later (for building from source)
- RyzenAI optional (build proceeds if missing)
- At least 8GB RAM recommended for multiple instances

### Build the Docker Image

From the repository root:

```bash
docker compose -f scripts/multi-server/docker-compose.yml build
```

This builds the `lemonade-server:latest` image from source, including:
- Multi-stage build with CMake compilation
- Vulkan backend support
- Resource files (server_models.json, etc.)

### Start Multiple Servers

```bash
docker compose -f scripts/multi-server/docker-compose.yml up -d
```

This starts three services:
- `llama-server` on port 8000
- `qwen-server` on port 8001  
- `phi-server` on port 8002

### Verify Deployment

Check container status:
```bash
docker compose -f scripts/multi-server/docker-compose.yml ps
```

Test health endpoints:
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health
curl http://localhost:8002/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "context_size": 4096,
  "model": "..."
}
```

### Stop Servers

```bash
docker compose -f scripts/multi-server/docker-compose.yml down
```

### Caveats and Known Issues

- **CMake Version**: Requires CMake ≥3.28.4. If your system has an older version, the build will fail.
- **RyzenAI**: Optional dependency. Build continues if RyzenAI SDK is not available.
- **Runtime Dependencies**: The runtime image includes `procps` for `pgrep` command used by the server.
- **Resources**: Critical files like `server_models.json` are copied from the build stage to the runtime image.
- **Memory**: Each container has a 4GB memory limit. Adjust in `docker-compose.yml` if needed.
- **Health Checks**: Internal health checks use `localhost`, which works within containers but may not be accessible externally if bound incorrectly.

### Customization

Edit `docker-compose.yml` to:
- Change ports or models
- Adjust memory limits
- Add environment variables
- Modify health check intervals

## Native Scripts Setup (Alternative)

If you prefer running directly on the host without Docker, use the PowerShell/Bash scripts below.

## Quick Start

### 1. Configure Your Servers

Edit `config/example-config.json` to define your server instances:

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

### 2. Validate Configuration

**Windows (PowerShell):**
```powershell
.\validate-config.ps1
```

**Linux/macOS (Bash):**
```bash
./validate-config.sh
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

### 4. Check Status

**Windows:**
```powershell
.\status-multi-server.ps1
```

**Linux/macOS:**
```bash
./status-multi-server.sh
```

### 5. Stop All Servers

**Windows:**
```powershell
.\stop-multi-server.ps1
```

**Linux/macOS:**
```bash
./stop-multi-server.sh
```

## Available Scripts

### Configuration Management

#### `validate-config` - Validate Configuration
Validates the JSON configuration file and checks port availability.

**Windows:**
```powershell
.\validate-config.ps1                          # Default: config/example-config.json
.\validate-config.ps1 config\my-config.json    # Custom config
.\validate-config.ps1 -SkipPortCheck           # Skip port availability checks
```

**Linux/macOS:**
```bash
./validate-config.sh                            # Default: config/example-config.json
./validate-config.sh config/my-config.json      # Custom config
./validate-config.sh --skip-port-check          # Skip port availability checks
```

### Server Lifecycle

#### `start-multi-server` - Start Servers
Starts all servers defined in the configuration file.

**Windows:**
```powershell
.\start-multi-server.ps1                       # Default config
.\start-multi-server.ps1 config\prod.json      # Custom config
.\start-multi-server.ps1 -Force                # Skip port checks
```

**Linux/macOS:**
```bash
./start-multi-server.sh                         # Default config
./start-multi-server.sh config/prod.json        # Custom config
./start-multi-server.sh --force                 # Skip port checks
```

**Output:**
- Each server runs in the background
- PID files saved in `pids/server-{port}.pid`
- Logs saved in `logs/server-{port}.log`
- Displays endpoints: `http://localhost:8000`, `http://localhost:8001`, etc.

#### `stop-multi-server` - Stop Servers
Stops all running servers gracefully.

**Windows:**
```powershell
.\stop-multi-server.ps1                        # Stop all servers
.\stop-multi-server.ps1 -Port 8000             # Stop specific server
.\stop-multi-server.ps1 -Force                 # Force kill if graceful shutdown fails
```

**Linux/macOS:**
```bash
./stop-multi-server.sh                          # Stop all servers
./stop-multi-server.sh --port 8000              # Stop specific server
./stop-multi-server.sh --force                  # Force kill if graceful shutdown fails
```

#### `restart-multi-server` - Restart Servers
Stops and then starts all servers.

**Windows:**
```powershell
.\restart-multi-server.ps1                     # Restart all with default config
.\restart-multi-server.ps1 -Port 8000          # Restart specific server
.\restart-multi-server.ps1 -ConfigFile config\prod.json -Force
```

**Linux/macOS:**
```bash
./restart-multi-server.sh                       # Restart all with default config
./restart-multi-server.sh --port 8000           # Restart specific server
./restart-multi-server.sh --config config/prod.json --force
```

### Monitoring

#### `status-multi-server` - Check Status
Checks if servers are running and queries their `/api/v1/health` endpoint.

**Windows:**
```powershell
.\status-multi-server.ps1                      # Check all servers
.\status-multi-server.ps1 -Port 8000           # Check specific server
.\status-multi-server.ps1 -Verbose             # Show loaded models
```

**Linux/macOS:**
```bash
./status-multi-server.sh                        # Check all servers
./status-multi-server.sh --port 8000            # Check specific server
./status-multi-server.sh --verbose              # Show loaded models
```

**Output:**
```
━━━ Server on Port 8000 ━━━
  Status: ✓ Running
  PID: 12345
  Uptime: 2h 15m
  Memory: 3456.78 MB
  Health Check: ✓ Healthy (ok)

━━━ Server on Port 8001 ━━━
  Status: ✓ Running
  PID: 12346
  Uptime: 2h 15m
  Memory: 2345.67 MB
  Health Check: ✓ Healthy (ok)
```

## Configuration Schema

See `config/server-config.schema.json` for the complete JSON schema.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier (alphanumeric, dash, underscore) |
| `port` | integer | Port number (1024-65535) |
| `model` | string | Model name (must be installed) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `llamacpp_backend` | string | `"vulkan"` | Backend: `vulkan`, `rocm`, or `cpu` |
| `ctx_size` | integer | `4096` | Context size (512-32768) |
| `log_level` | string | `"info"` | Log level: `debug`, `info`, `warning`, `error` |
| `host` | string | `"localhost"` | Host address to bind to |
| `max_loaded_models` | string | `"1 1 1 1"` | Max loaded models per type (LLM EMBEDDING RERANKING AUDIO) |
| `extra_args` | string | `""` | Additional CLI arguments |

## Directory Structure

```
scripts/multi-server/
├── config/
│   ├── server-config.schema.json    # JSON schema
│   └── example-config.json          # Example configuration
├── logs/
│   ├── server-8000.log              # Server logs (auto-generated)
│   └── server-8001.log
├── pids/
│   ├── server-8000.pid              # Process IDs (auto-generated)
│   └── server-8001.pid
├── start-multi-server.ps1           # Windows start script
├── start-multi-server.sh            # Linux start script
├── stop-multi-server.ps1            # Windows stop script
├── stop-multi-server.sh             # Linux stop script
├── restart-multi-server.ps1         # Windows restart script
├── restart-multi-server.sh          # Linux restart script
├── status-multi-server.ps1          # Windows status script
├── status-multi-server.sh           # Linux status script
├── validate-config.ps1              # Windows validator
├── validate-config.sh               # Linux validator
└── README.md                        # This file
```

## Prerequisites

### Windows (PowerShell)
- PowerShell 5.1 or later (PowerShell 7+ recommended)
- Lemonade Server installed (typically in `%LOCALAPPDATA%\lemonade_server\bin\`)

### Linux/macOS (Bash)
- Bash 4.0 or later
- `jq` for JSON parsing: `sudo apt-get install jq` (Ubuntu/Debian)
- `curl` or `wget` for health checks
- Lemonade Server installed (typically in `~/.local/bin/` or `/usr/local/bin/`)

## Common Use Cases

### Development: Test Multiple Models Simultaneously
```powershell
# Start 3 different models on ports 8000, 8001, 8002
.\start-multi-server.ps1

# Test each endpoint
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health
curl http://localhost:8002/api/v1/health
```

### Production: Run Specialized Models
```json
{
  "servers": [
    {
      "name": "chat-model",
      "port": 8000,
      "model": "Llama-3.2-3B-Instruct",
      "ctx_size": 8192
    },
    {
      "name": "code-model",
      "port": 8001,
      "model": "CodeLlama-7B",
      "ctx_size": 4096
    },
    {
      "name": "fast-model",
      "port": 8002,
      "model": "Qwen3-0.6B-GGUF",
      "ctx_size": 2048
    }
  ]
}
```

### Load Balancing: Route Requests to Different Instances
Use a reverse proxy (nginx, Caddy) to distribute traffic across multiple instances:

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

## Troubleshooting

### Port Already in Use
```
❌ Port 8000 is already in use
```

**Solution:**
1. Check what's using the port: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Linux)
2. Stop the conflicting process
3. Or change the port in `config/example-config.json`

### Server Won't Start
```
⚠️  Server 'llama-server' not running
```

**Solution:**
1. Check logs: `logs/server-8000.log`
2. Verify model is installed: `lemonade-server pull Llama-3.2-3B-Instruct`
3. Check lemonade-server path is correct

### Health Check Fails
```
❌ Unhealthy - Cannot reach health endpoint
```

**Solution:**
1. Server may still be starting (wait 10-30 seconds)
2. Check if server process is running: `.\status-multi-server.ps1`
3. Inspect logs for errors

### Out of Memory
```
Server crashed - insufficient memory
```

**Solution:**
1. Reduce `ctx_size` in configuration
2. Run fewer servers simultaneously
3. Use smaller models
4. Check system resources: `.\status-multi-server.ps1 -Verbose`

## Advanced Configuration

### Custom Model Paths
If models are in non-standard locations, use `extra_args`:

```json
{
  "name": "custom-model",
  "port": 8000,
  "model": "my-model",
  "extra_args": "--model-path /path/to/models"
}
```

### GPU/NPU Backend Selection
```json
{
  "name": "gpu-server",
  "port": 8000,
  "model": "Llama-3.2-3B-Instruct",
  "llamacpp_backend": "vulkan"   # or "rocm" for AMD GPUs, "cpu" for CPU-only
}
```

### Debug Mode
```json
{
  "name": "debug-server",
  "port": 8000,
  "model": "Qwen3-0.6B-GGUF",
  "log_level": "debug"
}
```

## API Endpoints

Each server instance exposes the standard Lemonade Server API:

- `GET /api/v1/health` - Health check
- `POST /api/v1/load` - Load a model
- `POST /api/v1/unload` - Unload a model
- `GET /api/v1/models` - List loaded models
- `POST /api/v1/chat/completions` - OpenAI-compatible chat
- `POST /api/v1/completions` - OpenAI-compatible completions

Full API documentation: https://lemonade-server.ai/docs/

## Docker Alternative

For containerized deployment, see `docker-compose.yml` for a Docker Compose setup.

## Support

- Documentation: https://lemonade-server.ai/docs/
- GitHub Issues: https://github.com/lemonade-server/lemonade/issues
- Specification: `../../specs/005-multi-llm-execution/`

## License

See main project LICENSE file.
