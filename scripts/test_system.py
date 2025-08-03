#!/usr/bin/env python3
"""
Voxtral System Test Script
Tests all components to ensure proper installation and configuration
"""

import sys
import os
import subprocess
import importlib
import requests
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test(name, status, details=""):
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {name}")
    if details:
        print(f"   {details}")

def test_python_dependencies():
    """Test if all Python dependencies are available"""
    print_header("Testing Python Dependencies")
    
    required_packages = [
        'yaml', 'numpy', 'sounddevice', 'webrtcvad', 'aiohttp',
        'langchain', 'langgraph', 'ddgs'
    ]
    
    optional_packages = [
        ('PyQt5', 'PyQt5.QtWidgets'),
        ('vllm', 'vllm'),
        ('faster_whisper', 'faster_whisper')
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print_test(f"Required: {package}", True)
        except ImportError as e:
            print_test(f"Required: {package}", False, f"Import error: {e}")
            all_good = False
    
    for display_name, import_name in optional_packages:
        try:
            importlib.import_module(import_name)
            print_test(f"Optional: {display_name}", True)
        except ImportError:
            print_test(f"Optional: {display_name}", False, "Not installed (optional)")
    
    return all_good

def test_system_tools():
    """Test if required system tools are available"""
    print_header("Testing System Tools")
    
    required_tools = ['python3', 'xdg-open']
    wayland_tools = ['wtype', 'wl-copy']
    x11_tools = ['xdotool', 'xclip']
    audio_tools = ['pulseaudio', 'pactl']
    
    all_good = True
    
    # Test required tools
    for tool in required_tools:
        try:
            subprocess.run(['which', tool], check=True, capture_output=True)
            print_test(f"Required: {tool}", True)
        except subprocess.CalledProcessError:
            print_test(f"Required: {tool}", False, "Not found in PATH")
            all_good = False
    
    # Test display server specific tools
    if os.environ.get('WAYLAND_DISPLAY'):
        print_test("Display Server", True, "Wayland detected")
        for tool in wayland_tools:
            try:
                subprocess.run(['which', tool], check=True, capture_output=True)
                print_test(f"Wayland: {tool}", True)
            except subprocess.CalledProcessError:
                print_test(f"Wayland: {tool}", False, "Install with: sudo apt install wtype wl-clipboard")
                all_good = False
    elif os.environ.get('DISPLAY'):
        print_test("Display Server", True, "X11 detected")
        for tool in x11_tools:
            try:
                subprocess.run(['which', tool], check=True, capture_output=True)
                print_test(f"X11: {tool}", True)
            except subprocess.CalledProcessError:
                print_test(f"X11: {tool}", False, "Install with: sudo apt install xdotool xclip")
    else:
        print_test("Display Server", False, "Neither Wayland nor X11 detected")
        all_good = False
    
    # Test audio tools
    for tool in audio_tools:
        try:
            subprocess.run(['which', tool], check=True, capture_output=True)
            print_test(f"Audio: {tool}", True)
        except subprocess.CalledProcessError:
            print_test(f"Audio: {tool}", False, "Audio system not properly configured")
    
    return all_good

def test_audio_system():
    """Test audio system functionality"""
    print_header("Testing Audio System")
    
    try:
        import sounddevice as sd
        
        # Test audio devices
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if input_devices:
            print_test("Audio Input Devices", True, f"Found {len(input_devices)} input device(s)")
            for i, device in enumerate(input_devices[:3]):  # Show first 3
                print(f"   - {device['name']}")
        else:
            print_test("Audio Input Devices", False, "No input devices found")
            return False
        
        # Test basic audio capture
        try:
            duration = 0.1  # Very short test
            sample_rate = 16000
            data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
            sd.wait()
            print_test("Audio Capture Test", True, f"Captured {len(data)} samples")
        except Exception as e:
            print_test("Audio Capture Test", False, f"Error: {e}")
            return False
        
        return True
        
    except ImportError:
        print_test("SoundDevice Module", False, "sounddevice not installed")
        return False
    except Exception as e:
        print_test("Audio System", False, f"Error: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print_header("Testing Configuration")
    
    try:
        from config.settings import config
        
        # Test basic config access
        endpoint = config.get("vllm_endpoint")
        model_name = config.get("model_name")
        
        print_test("Config Loading", True)
        print_test("VLLM Endpoint", bool(endpoint), f"Endpoint: {endpoint}")
        print_test("Model Name", bool(model_name), f"Model: {model_name}")
        
        # Test voice config
        voice_config = config.get("voice", {})
        sample_rate = voice_config.get("sample_rate", 0)
        print_test("Voice Config", sample_rate > 0, f"Sample rate: {sample_rate}Hz")
        
        return True
        
    except Exception as e:
        print_test("Configuration", False, f"Error: {e}")
        return False

def test_vllm_server():
    """Test VLLM server connectivity"""
    print_header("Testing VLLM Server")
    
    try:
        from config.settings import config
        endpoint = config.get("vllm_endpoint", "http://localhost:8000/v1")
        
        # Test server connectivity
        try:
            response = requests.get(f"{endpoint}/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                model_count = len(models.get('data', []))
                print_test("VLLM Server", True, f"Connected, {model_count} model(s) available")
                
                # Show available models
                for model in models.get('data', [])[:3]:  # Show first 3
                    print(f"   - {model.get('id', 'Unknown')}")
                
                return True
            else:
                print_test("VLLM Server", False, f"HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print_test("VLLM Server", False, "Connection refused - server not running")
            print("   Start with: vllm serve mistralai/Voxtral-Mini-3B-2507 --tokenizer_mode mistral --config_format mistral --load_format mistral")
            return False
        except requests.exceptions.Timeout:
            print_test("VLLM Server", False, "Connection timeout")
            return False
            
    except Exception as e:
        print_test("VLLM Server Test", False, f"Error: {e}")
        return False

def test_tools():
    """Test individual tools"""
    print_header("Testing Tools")
    
    try:
        # Test shell tool
        from tools.shell import run_shell
        result = run_shell.invoke({"command": "echo 'test'"})
        print_test("Shell Tool", "test" in result, f"Result: {result.strip()}")
        
        # Test web search tool
        try:
            from tools.web_search import search_web
            # Quick search test (may be slow)
            print("   Testing web search (this may take a moment)...")
            result = search_web.invoke({"query": "python", "max_results": 1})
            print_test("Web Search Tool", len(result) > 10, "Search completed")
        except Exception as e:
            print_test("Web Search Tool", False, f"Error: {e}")
        
        # Test typing tool (just import, don't actually type)
        from tools.cursor_typing import type_text, check_wayland_tools
        missing_tools = check_wayland_tools()
        if not missing_tools:
            print_test("Typing Tool", True, "Wayland tools available")
        else:
            print_test("Typing Tool", False, f"Missing: {', '.join(missing_tools)}")
        
        return True
        
    except Exception as e:
        print_test("Tools Test", False, f"Error: {e}")
        return False

def test_project_structure():
    """Test project structure"""
    print_header("Testing Project Structure")
    
    required_dirs = ['agent', 'tools', 'langraph', 'models', 'config', 'scripts']
    required_files = [
        'agent/agent_main.py',
        'agent/voice_processor.py',
        'models/vllm_handler.py',
        'langraph/workflows.py',
        'config/settings.py',
        'config/voxtral.yaml',
        'scripts/tray_icon.py',
        'requirements.txt'
    ]
    
    all_good = True
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        print_test(f"Directory: {dir_name}", exists)
        if not exists:
            all_good = False
    
    # Check files
    for file_name in required_files:
        file_path = project_root / file_name
        exists = file_path.exists() and file_path.is_file()
        print_test(f"File: {file_name}", exists)
        if not exists:
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print("🧠 Voxtral Agentic Voice Platform - System Test")
    print("=" * 60)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Python Dependencies", test_python_dependencies),
        ("System Tools", test_system_tools),
        ("Configuration", test_configuration),
        ("Audio System", test_audio_system),
        ("Tools", test_tools),
        ("VLLM Server", test_vllm_server),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_test(f"{test_name} (Exception)", False, f"Error: {e}")
            results[test_name] = False
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        print_test(test_name, result)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your Voxtral system is ready to use.")
        print("\nNext steps:")
        print("1. Start VLLM server (if not already running)")
        print("2. Launch tray: python scripts/tray_icon.py")
        print("3. Start agent from tray menu")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please address the issues above.")
        print("\nCommon fixes:")
        print("- Run: ./scripts/install.sh")
        print("- Install missing system packages")
        print("- Start VLLM server")
        print("- Check audio permissions")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)