# LiteLLM Proxy Server with OpenedAI Speech (RoCm)

Production-ready AI proxy infrastructure combining:
- **LiteLLM Proxy**: Multi-backend model routing and API gateway
- **OpenedAI Speech**: Text-to-Speech with RoCm GPU acceleration
- **Lemonade Server**: Local LLM inference backend
- **Nextcloud AI Integration**: End-to-end AI capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Nextcloud AI Integration App                               │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │ LiteLLM Proxy  │ (Port 4014)
                    │ (API Gateway)  │
                    └───────┬────────┘
                    ┌───────┴──────────────────┐
                    │                          │
        ┌───────────▼──────────────┐  ┌───────▼─────────────┐
        │ Lemonade Server          │  │ OpenedAI Speech     │
        │ (LLMs: Qwen, Phi, etc)   │  │ (TTS with RoCm)     │
        │ (Port 8000)              │  │ (Port 8888)         │
        └──────────────────────────┘  └─────────────────────┘
```

## Features

- **Multi-backend support**: Route to multiple LLM models and services
- **Model aliasing**: Simple names (llm-text-gen, llm-code-gen, tts-openedai)
- **GPU acceleration**: RoCm support for AMD GPUs (Radeon, RDNA, MI series)
- **Docker containers**: Simplified deployment and isolation
- **Windows Service**: Production-ready with auto-restart and health checking
- **Comprehensive logging**: Track all requests and performance

## Installation & Deployment

### 🔧 Production Installation (Windows Service)

**⚠️ Requires Administrator PowerShell**

```powershell
# Run PowerShell as Administrator
cd C:\path\to\lemonade

# Install LiteLLM as Windows Service
.\scripts\litellm\install-litellm-service.ps1 -Action install

# Check service status
.\scripts\litellm\install-litellm-service.ps1 -Action status
```

**Service Management:**
```powershell
# Start the service
.\scripts\litellm\install-litellm-service.ps1 -Action start

# Stop the service
.\scripts\litellm\install-litellm-service.ps1 -Action stop

# Restart with health check
.\scripts\litellm\install-litellm-service.ps1 -Action restart

# Check logs
Get-Content .\scripts\litellm\logs\litellm-service.log -Tail 20
```

**After Installation:**
- ✅ Service name: `LiteLLM-Proxy`
- ✅ Auto-starts on Windows boot
- ✅ Accessible at `http://localhost:4014`
- ✅ Master Key in service environment
- ✅ Logs in `.\scripts\litellm\logs\`

### 🐳 Development (Docker)

### Prerequisites

- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- Lemonade Server running on `localhost:8000`
- RoCm-compatible AMD GPU (for openedai-speech acceleration)

### Start Services with Docker

```powershell
# Navigate to scripts/litellm
cd scripts/litellm

# Start all services
.\manage-docker-services.ps1 -Action start -Service all

# Check status
.\manage-docker-services.ps1 -Action status

# View logs
.\manage-docker-services.ps1 -Action logs -Service litellm
.\manage-docker-services.ps1 -Action logs -Service openedai-speech
```

### Available Services

| Service | Port | URL |
|---------|------|-----|
| LiteLLM Proxy | 4014 | `http://localhost:4014` |
| OpenedAI Speech | 8888 | `http://localhost:8888` |
| Lemonade Server | 8000 | `http://localhost:8000` |

## Configuration

### Model Aliases (litellm-config.yaml)

Pre-configured aliases for easy use:

```yaml
# Text Generation
llm-text-gen       → Qwen3-Next-80B (powerful reasoning)
llm-code-gen       → Qwen3-Coder-30B (code generation)
llm-text-fast      → Gemma-3-4b (quick responses)
llm-instruct       → Phi-4-mini (instruction following)

# Audio
audio-transcription → Whisper-Large-v3-Turbo (speech-to-text)

# Text-to-Speech
tts-openedai       → OpenedAI Speech with RoCm (TTS)
```

### Docker Compose Configuration

Edit `docker-compose.yml` to customize:

- **GPU device**: `CUDA_VISIBLE_DEVICES` in openedai-speech service
- **Memory limits**: Add `mem_limit` to service config
- **Log rotation**: Already configured with 10MB max, 3 files
- **Network**: Uses internal `lemonade-network` bridge

## API Usage

### Chat Completions (via LiteLLM)

```bash
curl -X POST http://localhost:4014/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234567890abcdefghijklmnopqrstuv" \
  -d '{
    "model": "llm-text-gen",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 256
  }'
```

### Text-to-Speech (via OpenedAI Speech)

```bash
curl -X POST http://localhost:8888/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, this is a test",
    "voice": "alloy"
  }' \
  --output speech.mp3
```

### List Available Models

```bash
curl http://localhost:4014/v1/models \
  -H "Authorization: Bearer sk-1234567890abcdefghijklmnopqrstuv"
```

## Management Commands

```powershell
# Start services
.\manage-docker-services.ps1 -Action start

# Stop services
.\manage-docker-services.ps1 -Action stop

# Restart services
.\manage-docker-services.ps1 -Action restart

# Check status and health
.\manage-docker-services.ps1 -Action status

# View container logs
.\manage-docker-services.ps1 -Action logs -Service litellm
.\manage-docker-services.ps1 -Action logs -Service openedai-speech

# Pull latest images
.\manage-docker-services.ps1 -Action pull
```

## GPU Setup (RoCm)

### Requirements

- AMD GPU: Radeon RX 7000 series, RDNA 3/2, MI series
- ROCm drivers installed (usually via Docker image)
- Sufficient VRAM: 8GB+ recommended

### Verify GPU Access

```bash
# Check if GPU is accessible
docker run --rm --device=/dev/kfd --device=/dev/dri \
  ghcr.io/matatonic/openedai-speech:rocm \
  rocminfo | grep "GPU"

# Monitor GPU usage during inference
rocm-smi watch
```

## Troubleshooting

### Services Won't Start

```powershell
# Check Docker is running
docker ps

# Check logs
.\manage-docker-services.ps1 -Action logs -Service litellm

# Restart Docker and retry
docker restart litellm-proxy openedai-speech-rocm
```

### GPU Not Being Used

```powershell
# Check GPU detection
docker exec openedai-speech-rocm rocminfo

# Verify in logs
.\manage-docker-services.ps1 -Action logs -Service openedai-speech | 
  findstr /I "GPU device cuda rocm"
```

### Port Conflicts

If ports 4014 or 8888 are already in use:

1. Edit `docker-compose.yml`
2. Change `ports:` section:
   ```yaml
   # LiteLLM - change first port
   ports:
     - "8089:4000"  # Now accessible on localhost:8089
   
   # OpenedAI Speech - change first port
   ports:
     - "8887:8000"  # Now accessible on localhost:8887
   ```
3. Update `litellm-config.yaml` with new ports
4. Restart services

### Memory Issues

```yaml
# In docker-compose.yml, add to service:
mem_limit: "16g"
memswap_limit: "20g"
```

## Integration with Nextcloud

1. Install Nextcloud AI Integration app
2. Configure AI Provider:
   - **Provider URL**: `http://your-server:4014`
   - **API Key**: `sk-1234567890abcdefghijklmnopqrstuv` (or set in config)
   - **Models Available**:
     - `llm-text-gen` (Text Generation)
     - `llm-code-gen` (Code Generation)
     - `tts-openedai` (Text-to-Speech)
     - `audio-transcription` (Speech-to-Text)

3. Test in Nextcloud:
   - Create a new text document
   - Use "AI" menu to generate content
   - Or use voice commands for audio transcription

## Production Deployment

For production on internal network (192.168.86.196):

1. Use Apache reverse proxy on DMZ (see `configs/apache-api-proxy.conf`)
2. Configure SSL/TLS certificates
3. Set strong API key in `litellm-config.yaml`
4. Enable database logging for audit trail
5. Set up monitoring (Prometheus/Grafana)
6. Configure key rotation policy

See: `specs/006-nextcloud-litellm-infra/` for complete infrastructure spec

## Documentation

- [LiteLLM Official Docs](https://docs.litellm.ai/)
- [OpenedAI Speech GitHub](https://github.com/matatonic/openedai-speech)
- [RoCm Documentation](https://rocmdocs.amd.com/)
- [Nextcloud AI Integration](https://apps.nextcloud.com/)

## Support

For issues:
1. Check service logs with `manage-docker-services.ps1 -Action logs`
2. Verify Lemonade Server is running and accessible
3. Check GPU availability with `rocminfo`
4. Review Docker resource limits and memory usage
5. Consult project repository issues

## License

See LICENSE file in project root
