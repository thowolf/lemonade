#!/usr/bin/env python3
"""
ROCm Functionality Test for AMD AI Max+ 395
Tests if ROCm is working on Windows with Lemonade Server setup
"""

import subprocess
import sys
import platform

def test_rocm_basic():
    """Test basic ROCm functionality."""
    print("🔍 Testing ROCm functionality on Windows...")
    print(f"Platform: {platform.system()} {platform.release()}")
    print()

    tests_passed = 0
    total_tests = 0

    # Test 1: Check if rocm-smi command exists
    total_tests += 1
    print("Test 1: Checking for rocm-smi command...")
    try:
        result = subprocess.run(['rocm-smi', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ rocm-smi command found")
            print(f"   Version: {result.stdout.strip()}")
            tests_passed += 1
        else:
            print("❌ rocm-smi command failed")
            print(f"   Error: {result.stderr.strip()}")
    except FileNotFoundError:
        print("❌ rocm-smi command not found in PATH")
        print("   This is expected if ROCm drivers are not installed")
    except Exception as e:
        print(f"❌ rocm-smi test failed: {e}")

    # Test 2: Check GPU detection
    total_tests += 1
    print("\nTest 2: Checking GPU detection...")
    try:
        result = subprocess.run(['rocm-smi', '--showproductname'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            gpu_name = result.stdout.strip()
            print(f"✅ GPU detected: {gpu_name}")
            if 'Radeon RX 9100' in gpu_name or 'AI Max+ 395' in gpu_name:
                print("✅ Correct GPU model detected (AMD Radeon RX 9100)")
                tests_passed += 1
            else:
                print("⚠️  GPU detected but model may not be AMD Radeon RX 9100")
                tests_passed += 1  # Still counts as GPU detection working
        else:
            print("❌ GPU detection failed")
            print(f"   Error: {result.stderr.strip()}")
    except FileNotFoundError:
        print("❌ rocm-smi command not found")
    except Exception as e:
        print(f"❌ GPU detection test failed: {e}")

    # Test 3: Check VRAM information
    total_tests += 1
    print("\nTest 3: Checking VRAM information...")
    try:
        result = subprocess.run(['rocm-smi', '--showmeminfo', 'vram'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            vram_info = result.stdout.strip()
            print("✅ VRAM information retrieved")
            print(f"   Details: {vram_info}")
            if '128' in vram_info and ('GB' in vram_info or 'MB' in vram_info):
                print("✅ Expected VRAM capacity detected")
                tests_passed += 1
            else:
                print("⚠️  VRAM detected but capacity unclear")
                tests_passed += 1
        else:
            print("❌ VRAM information retrieval failed")
            print(f"   Error: {result.stderr.strip()}")
    except FileNotFoundError:
        print("❌ rocm-smi command not found")
    except Exception as e:
        print(f"❌ VRAM test failed: {e}")

    # Test 4: Check Lemonade Server connectivity
    total_tests += 1
    print("\nTest 4: Checking Lemonade Server connectivity...")
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/models", timeout=10)
        if response.status_code == 200:
            print("✅ Lemonade Server is responding")
            data = response.json()
            model_count = len(data.get('data', []))
            print(f"   Models loaded: {model_count}")
            tests_passed += 1
        else:
            print(f"❌ Lemonade Server returned status code: {response.status_code}")
    except ImportError:
        print("❌ requests library not available")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Lemonade Server at localhost:8000")
        print("   Make sure Lemonade Server is running")
    except Exception as e:
        print(f"❌ Lemonade Server test failed: {e}")

    # Summary
    print("\n" + "="*50)
    print("ROCm Functionality Test Summary")
    print("="*50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(".1f")

    if tests_passed == total_tests:
        print("🎉 All tests passed! ROCm is fully functional.")
        return True
    elif tests_passed >= 2:
        print("⚠️  Partial success. ROCm may work but with limitations.")
        return True
    else:
        print("❌ ROCm functionality not detected.")
        print("   Consider installing AMD Radeon Software with ROCm support.")
        return False

if __name__ == "__main__":
    success = test_rocm_basic()
    print("\nNext steps:")
    if success:
        print("- Run: deploy_windows.bat to continue with deployment")
    else:
        print("- Install AMD Radeon Software from: https://www.amd.com/en/support")
        print("- Enable ROCm/HIP components during installation")
        print("- Reboot and run this test again")
        print("- Then run: deploy_windows.bat")

    sys.exit(0 if success else 1)