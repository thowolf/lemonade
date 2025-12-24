# Manual ROCm Installation Guide for AMD AI Max+ 395 (Windows)

## Current Status: AMD-SMI Doesn't Support Windows

**Important Finding**: The `rocm_smi_lib` repository you found is deprecated and has been replaced by `AMD-SMI`. However, **AMD-SMI only supports Linux** - not Windows.

From the AMD-SMI documentation:
> "This project is applicable to Linux Baremetal and Linux VM(Guest)"

## Windows ROCm Reality

ROCm on Windows is **not officially supported** by AMD. However, since you already have Lemonade Server running on Windows, ROCm functionality might be available through:

1. **Lemonade Server's built-in ROCm support**
2. **AMD GPU drivers with HIP support**
3. **Third-party ROCm implementations**

## Recommended Windows Installation Steps

### Step 1: Check Your Current Setup
Since Lemonade Server is already installed, let's verify ROCm functionality:

```cmd
# Open Command Prompt or PowerShell as Administrator
cd C:\AMD_Max395_Deployment

# Test if ROCm tools are available
rocm-smi --version
rocm-smi --showproductname
rocm-smi --showmeminfo vram
```

**Expected Results:**
```
ROCm System Management Interface: [version]
==============================
AMD Radeon RX 9100
==============================
GPU Memory Usage: 0% (0/131072 MB)
```

### Step 2: If ROCm Works
If the above commands work, ROCm is already functional! Skip to deployment.

### Step 3: If ROCm Doesn't Work
Install/update AMD GPU drivers:

#### Option A: AMD Radeon Software (Recommended)
1. **Visit**: https://www.amd.com/en/support/graphics/radeon-9000-series/radeon-rx-9000-series/amd-radeon-rx-9100
2. **Download**: "Radeon Software for Windows"
3. **Install** as Administrator
4. **Enable** experimental features if available
5. **Reboot** and test again

#### Option B: OEM Drivers
If your AMD AI Max+ 395 came with your system:
1. Check your system manufacturer's website
2. Download OEM-specific AMD drivers
3. Install with ROCm/HIP components enabled

#### Option C: Beta/Development Drivers
1. **Visit**: https://www.amd.com/en/support/kb/release-notes/rn-rad-win-24-12-1
2. **Download**: Latest beta drivers
3. Look for "ROCm" or "HIP" in feature list

### Step 4: Alternative: Use Linux VM
For full ROCm support, consider:
1. **Install Windows Subsystem for Linux (WSL2)**
2. **Install Ubuntu in WSL2**
3. **Install ROCm in the Linux environment**
4. **Run testing framework in WSL2**

## Lemonade Server ROCm Integration

Since you have Lemonade Server installed, check its configuration:

1. **Open**: `C:\Users\tomwo\AppData\Local\lemonade_server\config.yaml`
2. **Verify ROCm settings**:
```yaml
rocm:
  enabled: true
  gpu_device: 0
  vram_budget: 120
```

## Testing ROCm Functionality

Create a test script to verify ROCm works with your setup:

```python
# Save as test_rocm.py
import subprocess
import sys

def test_rocm():
    try:
        # Test rocm-smi
        result = subprocess.run(['rocm-smi', '--showproductname'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and 'Radeon RX 9100' in result.stdout:
            print("✅ ROCm detected: AMD Radeon RX 9100")
            return True
        else:
            print("❌ ROCm not working or GPU not detected")
            return False
    except FileNotFoundError:
        print("❌ rocm-smi command not found")
        return False
    except Exception as e:
        print(f"❌ ROCm test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_rocm()
    sys.exit(0 if success else 1)
```

Run with: `python test_rocm.py`

## Continue Deployment

Once ROCm is working (or if you want to proceed with CPU-only testing):

```cmd
cd C:\AMD_Max395_Deployment
deploy_windows.bat
```

## Performance Expectations

- **With ROCm**: Full GPU acceleration, 50+ tokens/sec
- **Without ROCm**: CPU-only mode, significantly slower performance
- **Lemonade Server**: Should work regardless of ROCm status

## Support Resources

- **AMD Community Forums**: Search for "Radeon RX 9100 ROCm Windows"
- **Lemonade Server Issues**: Check their GitHub for Windows-specific issues
- **AMD Developer Forums**: Ask about Windows ROCm support

## Summary

**Current Status**: AMD-SMI (successor to rocm_smi_lib) doesn't support Windows.
**Your Setup**: Lemonade Server may already provide ROCm functionality.
**Recommendation**: Test current setup first, then install AMD drivers if needed.

The testing framework will work regardless - it will just be slower without GPU acceleration.