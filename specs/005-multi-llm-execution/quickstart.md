# Quick Start: Mehrere Lemonade Server Instanzen parallel ausführen

**Feature**: 005-multi-llm-execution  
**Status**: Deployment-Lösung - Sofort verwendbar  
**Date**: 2026-01-09

## Überblick

Diese Anleitung zeigt, wie Sie mehrere Lemonade Server Instanzen gleichzeitig auf verschiedenen Ports laufen lassen, sodass jede Instanz ein eigenes Modell bereitstellt.

## Voraussetzungen

- Lemonade Server installiert
- Modelle heruntergeladen via `lemonade-server pull MODEL_NAME`
- Ausreichend RAM/VRAM für mehrere Modelle (empfohlen: 32GB+ System RAM)
- Freie Ports (z.B. 8000, 8001, 8002)

## Methode 1: Manuell (Einfach, für Tests)

### Schritt 1: Erste Server-Instanz starten

**Terminal 1** (PowerShell):
```powershell
# Server auf Port 8000 mit Modell Llama-3.2-3B-Instruct
$env:LEMONADE_PORT = "8000"
lemonade-server run Llama-3.2-3B-Instruct --port 8000 --log-level debug
```

### Schritt 2: Zweite Server-Instanz starten

**Terminal 2** (neues PowerShell-Fenster):
```powershell
# Server auf Port 8001 mit Modell Qwen3-0.6B-GGUF
$env:LEMONADE_PORT = "8001"
lemonade-server run Qwen3-0.6B-GGUF --port 8001 --log-level debug
```

### Schritt 3: Dritte Server-Instanz starten

**Terminal 3** (neues PowerShell-Fenster):
```powershell
# Server auf Port 8002 mit Modell Phi-4-mini
$env:LEMONADE_PORT = "8002"
lemonade-server run Phi-4-mini --port 8002 --log-level debug
```

### Schritt 4: Server testen

```powershell
# Test Server 1 (Port 8000)
curl http://localhost:8000/api/v1/health | ConvertFrom-Json

# Test Server 2 (Port 8001)
curl http://localhost:8001/api/v1/health | ConvertFrom-Json

# Test Server 3 (Port 8002)
curl http://localhost:8002/api/v1/health | ConvertFrom-Json
```

### Schritt 5: Inference-Anfragen senden

```python
import openai

# Client für Server 1 (Port 8000 - Llama)
client1 = openai.OpenAI(base_url="http://localhost:8000/api/v1", api_key="dummy")
response1 = client1.chat.completions.create(
    model="Llama-3.2-3B-Instruct",
    messages=[{"role": "user", "content": "Erkläre Quantencomputing"}]
)
print("Llama:", response1.choices[0].message.content)

# Client für Server 2 (Port 8001 - Qwen)
client2 = openai.OpenAI(base_url="http://localhost:8001/api/v1", api_key="dummy")
response2 = client2.chat.completions.create(
    model="Qwen3-0.6B-GGUF",
    messages=[{"role": "user", "content": "Was ist maschinelles Lernen?"}]
)
print("Qwen:", response2.choices[0].message.content)

# Client für Server 3 (Port 8002 - Phi)
client3 = openai.OpenAI(base_url="http://localhost:8002/api/v1", api_key="dummy")
response3 = client3.chat.completions.create(
    model="Phi-4-mini",
    messages=[{"role": "user", "content": "Schreibe Python Code für Fibonacci"}]
)
print("Phi:", response3.choices[0].message.content)
```

Alle drei Anfragen werden parallel verarbeitet!

## Methode 2: Automatisiert mit PowerShell-Skript (Empfohlen)

### Konfigurationsdatei erstellen

Erstellen Sie `multi-server-config.json`:

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
    },
    {
      "name": "phi-server",
      "port": 8002,
      "model": "Phi-4-mini",
      "llamacpp_backend": "vulkan",
      "ctx_size": 4096,
      "log_level": "info"
    }
  ]
}
```

### Start-Skript erstellen

Erstellen Sie `start-multi-server.ps1`:

```powershell
# Multi-Server Starter Script
param(
    [string]$ConfigFile = "multi-server-config.json"
)

# Lade Konfiguration
$config = Get-Content $ConfigFile | ConvertFrom-Json

# Erstelle Verzeichnisse für Logs und PIDs
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "pids" | Out-Null

Write-Host "=== Starting Multiple Lemonade Server Instances ===" -ForegroundColor Green

foreach ($server in $config.servers) {
    Write-Host "`nStarting $($server.name) on port $($server.port)..." -ForegroundColor Cyan
    
    # Prüfe ob Port bereits belegt
    $portCheck = Get-NetTCPConnection -LocalPort $server.port -ErrorAction SilentlyContinue
    if ($portCheck) {
        Write-Host "ERROR: Port $($server.port) is already in use!" -ForegroundColor Red
        continue
    }
    
    # Baue Befehl
    $logFile = "logs\server-$($server.port).log"
    $pidFile = "pids\server-$($server.port).pid"
    
    $arguments = @(
        "run",
        $server.model,
        "--port", $server.port,
        "--llamacpp", $server.llamacpp_backend,
        "--ctx-size", $server.ctx_size,
        "--log-level", $server.log_level,
        "--no-tray"
    )
    
    # Starte Server im Hintergrund
    $process = Start-Process `
        -FilePath "lemonade-server" `
        -ArgumentList $arguments `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput $logFile
    
    # Speichere PID
    $process.Id | Out-File $pidFile
    
    Write-Host "Started $($server.name) (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "  Port: $($server.port)" -ForegroundColor Gray
    Write-Host "  Model: $($server.model)" -ForegroundColor Gray
    Write-Host "  Log: $logFile" -ForegroundColor Gray
}

Write-Host "`n=== All servers started ===" -ForegroundColor Green
Write-Host "Run './status-servers.ps1' to check status" -ForegroundColor Yellow
Write-Host "Run './stop-servers.ps1' to stop all servers" -ForegroundColor Yellow
```

### Status-Skript erstellen

Erstellen Sie `status-servers.ps1`:

```powershell
# Multi-Server Status Script

Write-Host "=== Lemonade Server Instances Status ===" -ForegroundColor Green

Get-ChildItem "pids\*.pid" -ErrorAction SilentlyContinue | ForEach-Object {
    $port = $_.Name -replace 'server-|\.pid'
    $pid = Get-Content $_.FullName
    
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "`n✓ Server on port $port (PID: $pid)" -ForegroundColor Green
        
        # Teste Health Endpoint
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:$port/api/v1/health" -Method Get
            Write-Host "  Status: $($health.status)" -ForegroundColor Cyan
            if ($health.all_models_loaded -and $health.all_models_loaded.Count -gt 0) {
                Write-Host "  Model: $($health.all_models_loaded[0].model_name)" -ForegroundColor Cyan
                Write-Host "  Type: $($health.all_models_loaded[0].type)" -ForegroundColor Cyan
                Write-Host "  Device: $($health.all_models_loaded[0].device)" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "  Status: Server läuft, aber API nicht erreichbar" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n✗ Server on port $port (not running)" -ForegroundColor Red
    }
}
```

### Stop-Skript erstellen

Erstellen Sie `stop-servers.ps1`:

```powershell
# Multi-Server Stop Script

Write-Host "=== Stopping All Lemonade Server Instances ===" -ForegroundColor Yellow

Get-ChildItem "pids\*.pid" -ErrorAction SilentlyContinue | ForEach-Object {
    $port = $_.Name -replace 'server-|\.pid'
    $pid = Get-Content $_.FullName
    
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "Stopping server on port $port (PID: $pid)..." -ForegroundColor Cyan
        Stop-Process -Id $pid -Force
        Write-Host "  Stopped" -ForegroundColor Green
    }
    
    # Lösche PID-Datei
    Remove-Item $_.FullName
}

Write-Host "`n=== All servers stopped ===" -ForegroundColor Green
```

### Verwendung

```powershell
# Alle Server starten
./start-multi-server.ps1

# Status prüfen
./status-servers.ps1

# Alle Server stoppen
./stop-servers.ps1
```

## Methode 3: Mit Docker Compose (Optional)

Erstellen Sie `docker-compose.yml`:

```yaml
version: '3.8'

services:
  lemonade-llama:
    image: lemonade-server:latest
    ports:
      - "8000:8000"
    environment:
      - LEMONADE_PORT=8000
    command: run Llama-3.2-3B-Instruct --port 8000 --no-tray
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface

  lemonade-qwen:
    image: lemonade-server:latest
    ports:
      - "8001:8001"
    environment:
      - LEMONADE_PORT=8001
    command: run Qwen3-0.6B-GGUF --port 8001 --no-tray
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface

  lemonade-phi:
    image: lemonade-server:latest
    ports:
      - "8002:8002"
    environment:
      - LEMONADE_PORT=8002
    command: run Phi-4-mini --port 8002 --no-tray
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
```

```powershell
# Alle Server starten
docker-compose up -d

# Status prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down
```

## Fehlerbehebung

**Problem**: Port bereits belegt  
**Lösung**: Prüfen Sie mit `Get-NetTCPConnection -LocalPort 8000` und wählen Sie einen anderen Port

**Problem**: Out of Memory beim Starten mehrerer Server  
**Lösung**: Verwenden Sie kleinere Modelle oder erhöhen Sie System-RAM

**Problem**: NPU-Konflikt  
**Lösung**: Nur ein Server darf NPU-Backend (oga-npu, flm, oga-hybrid) verwenden, andere müssen GPU/CPU nutzen

**Problem**: Server startet nicht im Hintergrund  
**Lösung**: Verwenden Sie `--no-tray` Flag, um Tray-App zu deaktivieren

## Nächste Schritte

- **Load Balancing**: Nutzen Sie nginx als Reverse Proxy für Load Balancing zwischen Servern
- **Monitoring**: Integrieren Sie Prometheus für Metriken-Sammlung von allen Instanzen
- **Auto-Restart**: Verwenden Sie Windows Task Scheduler oder systemd für Auto-Restart bei Crashes
