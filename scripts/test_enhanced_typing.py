#!/usr/bin/env python3
"""
Test script for enhanced cursor typing capabilities
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_available_tools():
    """Test which typing tools are available"""
    tools = ['wtype', 'ydotool', 'xdotool', 'wl-copy', 'xclip']
    available = {}
    
    print("🔧 Testing available typing tools:")
    for tool in tools:
        try:
            result = subprocess.run(['which', tool], capture_output=True, text=True)
            available[tool] = result.returncode == 0
            status = "✅" if available[tool] else "❌"
            print(f"  {status} {tool}")
        except:
            available[tool] = False
            print(f"  ❌ {tool}")
    
    return available

def test_wtype_typing():
    """Test wtype direct typing"""
    if not os.environ.get('WAYLAND_DISPLAY'):
        print("⚠️ Not on Wayland, skipping wtype test")
        return False
    
    print("\n🎯 Testing wtype direct typing...")
    print("   Please focus a text editor and wait 3 seconds...")
    time.sleep(3)
    
    try:
        test_text = "Hello from wtype! This is a test of direct typing."
        result = subprocess.run(['wtype', test_text], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print(f"   ✅ wtype success: typed {len(test_text)} characters")
            return True
        else:
            print(f"   ❌ wtype failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ wtype error: {e}")
        return False

def test_ydotool_typing():
    """Test ydotool direct typing"""
    print("\n🎯 Testing ydotool direct typing...")
    print("   Please focus a text editor and wait 3 seconds...")
    time.sleep(3)
    
    try:
        # Check if ydotool daemon is running
        daemon_check = subprocess.run(['pgrep', 'ydotoold'], capture_output=True)
        if daemon_check.returncode != 0:
            print("   ⚠️ ydotool daemon not running, trying to start...")
            # Note: This might need sudo in real usage
            
        test_text = "Hello from ydotool! This is root-level injection."
        result = subprocess.run(['ydotool', 'type', test_text], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print(f"   ✅ ydotool success: typed {len(test_text)} characters")
            return True
        else:
            print(f"   ❌ ydotool failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ ydotool error: {e}")
        return False

def test_clipboard_method():
    """Test clipboard + paste method"""
    print("\n📋 Testing clipboard + paste method...")
    print("   Please focus a text editor and wait 3 seconds...")
    time.sleep(3)
    
    try:
        test_text = "Hello from clipboard! This is the fallback method."
        
        # Copy to clipboard
        if os.environ.get('WAYLAND_DISPLAY'):
            proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=test_text, timeout=5)
            clipboard_success = proc.returncode == 0
        else:
            proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=test_text, timeout=5)
            clipboard_success = proc.returncode == 0
        
        if not clipboard_success:
            print("   ❌ Failed to copy to clipboard")
            return False
        
        print(f"   ✅ Copied to clipboard: {len(test_text)} characters")
        
        # Try to paste
        time.sleep(0.5)
        if os.environ.get('WAYLAND_DISPLAY'):
            # Try ydotool first
            result = subprocess.run(['ydotool', 'key', 'ctrl+v'], capture_output=True, timeout=3)
            if result.returncode == 0:
                print("   ✅ Pasted using ydotool")
                return True
            
            # Try wtype
            result = subprocess.run(['wtype', '-M', 'ctrl', 'v'], capture_output=True, timeout=3)
            if result.returncode == 0:
                print("   ✅ Pasted using wtype")
                return True
        else:
            result = subprocess.run(['xdotool', 'key', 'ctrl+v'], capture_output=True, timeout=3)
            if result.returncode == 0:
                print("   ✅ Pasted using xdotool")
                return True
        
        print("   ⚠️ Clipboard copy successful, but auto-paste failed")
        print("   💡 You can manually press Ctrl+V to paste the text")
        return True
        
    except Exception as e:
        print(f"   ❌ Clipboard method error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Enhanced Cursor Typing Test Suite")
    print("=" * 50)
    
    # Test available tools
    available_tools = test_available_tools()
    
    # Display environment info
    display_server = "Wayland" if os.environ.get('WAYLAND_DISPLAY') else "X11" if os.environ.get('DISPLAY') else "Unknown"
    print(f"\n🖥️ Display server: {display_server}")
    
    # Test methods based on availability
    success_count = 0
    total_tests = 0
    
    if available_tools.get('wtype') and os.environ.get('WAYLAND_DISPLAY'):
        total_tests += 1
        if test_wtype_typing():
            success_count += 1
    
    if available_tools.get('ydotool'):
        total_tests += 1
        if test_ydotool_typing():
            success_count += 1
    
    # Always test clipboard method
    total_tests += 1
    if test_clipboard_method():
        success_count += 1
    
    # Summary
    print(f"\n📊 Test Results: {success_count}/{total_tests} methods successful")
    
    if success_count > 0:
        print("✅ Enhanced cursor typing is working!")
        print("💡 The system will automatically choose the best available method")
    else:
        print("❌ No typing methods are working")
        print("🔧 Please check your system configuration")

if __name__ == "__main__":
    main()