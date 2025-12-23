# ROCm Max395 Setup Guide

**Feature**: AMD AI Max+ 395 ROCm Testing
**Purpose**: Complete setup instructions for ROCm backend testing on Windows 11

## Prerequisites

- Windows 11 (build 22H2+) with administrator access
- AMD AI Max+ 395 GPU (gfx1151 architecture, 128GB VRAM)
- Internet connection for downloads
- 200GB+ free disk space

## Step 1: Install AMD ROCm Drivers

### Download HIP SDK

1. Visit: https://rocm.docs.amd.com/projects/install-on-windows/en/latest/
2. Download latest HIP SDK installer (7.1.1 or newer)
3. Size: ~2-3 GB

### Install with Administrator Privileges

```powershell
# Run installer as Administrator
# Accept license, choose default installation path
# Installation path typically: C:\Program Files\AMD\ROCm\
```

### Verify Installation

```powershell
# Open PowerShell as Administrator
rocminfo
# Should display: AMD AI Max+ 395, gfx1151 architecture, 128 GB VRAM

hipinfo
# Should show HIP version and device information
```

**Troubleshooting**:
- If `rocminfo` not found: Add `C:\Program Files\AMD\ROCm\bin` to PATH
- If GPU not detected: Update AMD graphics drivers from AMD.com
- If architecture mismatch: Set `HSA_OVERRIDE_GFX_VERSION=11.5.1`

## Step 2: Install Lemonade Server

### Option A: Windows MSI Installer (Recommended)

1. Visit: https://github.com/lemonade-sdk/lemonade/releases/latest
2. Download: `lemonade-server-minimal.msi`
3. Run MSI installer and accept defaults
4. Installation adds Lemonade to PATH automatically

### Option B: From Source (Advanced)

```powershell
git clone https://github.com/lemonade-sdk/lemonade.git
cd lemonade
python -m pip install -e .
```

### Verify Installation

```powershell
lemonade-server --version
# Should show: 9.1.1 or newer
```

## Step 3: Setup Python Environment

### Create Virtual Environment (Recommended)

```powershell
# Navigate to repository root
cd C:\path\to\lemonade

# Create virtual environment
python -m venv venv-rocm-test
.\venv-rocm-test\Scripts\Activate.ps1

# Install test dependencies
cd tests\rocm_max395
pip install -r requirements.txt
```

### Verify Python Version

```powershell
python --version
# Should be: Python 3.10.x, 3.11.x, 3.12.x, or 3.13.x
```

## Step 4: Download Test Models

### Pull Small Test Model

```powershell
# Download Llama 3.2 1B for initial testing
lemonade-server pull Llama-3.2-1B-Instruct-GGUF

# Wait for download (~700 MB)
# Model saved to: %USERPROFILE%\.lemonade\models\
```

### Verify Model Download

```powershell
lemonade-server list
# Should show: Llama-3.2-1B-Instruct-GGUF [downloaded]
```

## Step 5: First Test Run

### Start Lemonade Server

```powershell
# Start server with ROCm backend
lemonade-server run Llama-3.2-1B-Instruct-GGUF --llamacpp rocm

# Expected output:
# [INFO] Loading model: Llama-3.2-1B-Instruct-GGUF
# [INFO] Using backend: ROCm (gfx1151)
# [INFO] Model loaded (VRAM: 2.3 GB)
# [INFO] Server running at http://localhost:8000
```

### Run Basic Test

```powershell
# In another terminal
cd tests\rocm_max395
pytest test_basic_inference.py::test_single_prompt_generation -v

# Expected: PASSED
```

## Environment Variables

Set these if needed:

```powershell
# Force GFX version for Max+ 395
set HSA_OVERRIDE_GFX_VERSION=11.5.1

# Add ROCm to PATH
set PATH=%PATH%;C:\Program Files\AMD\ROCm\bin

# Lemonade model directory
set LEMONADE_MODELS_DIR=%USERPROFILE%\.lemonade\models
```

## Troubleshooting

### ROCm Issues
- **GPU not detected**: Update Windows AMD drivers
- **HIP not found**: Reinstall ROCm SDK, check PATH
- **Architecture mismatch**: Set HSA_OVERRIDE_GFX_VERSION

### Lemonade Issues
- **Server won't start**: Check ROCm installation, try CPU backend first
- **Model loading fails**: Verify model download, check disk space
- **API errors**: Ensure server is running on correct port (8000)

### Python Issues
- **Import errors**: Activate virtual environment, reinstall requirements
- **Version conflicts**: Use Python 3.10-3.13 only

## Next Steps

After setup verification, proceed to run the full test suite:

```powershell
# Run all tests
pytest -v

# Run specific user story
pytest test_basic_inference.py -v  # P1
pytest test_performance.py -v      # P2
pytest test_rag_integration.py -v  # P3
pytest test_multi_model.py -v      # P4
```