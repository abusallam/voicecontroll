#!/usr/bin/env python3
"""
Interactive Cursor Typing Test Script
Tests cursor typing functionality with user feedback
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.cursor_typing import type_text, paste_text

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def get_user_input(prompt):
    """Get user input with a prompt"""
    return input(f"\n{prompt}: ").strip()

def wait_for_user(message):
    """Wait for user to press Enter"""
    input(f"\n{message} (Press Enter when ready)")

def test_clipboard_functionality():
    """Test basic clipboard functionality"""
    print_header("Testing Clipboard Functionality")
    
    test_text = "Hello from clipboard test!"
    
    print(f"Testing clipboard with text: '{test_text}'")
    
    # Test copying to clipboard
    try:
        if os.environ.get('WAYLAND_DISPLAY'):
            proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=test_text, timeout=5)
            copy_success = proc.returncode == 0
        else:
            proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=test_text, timeout=5)
            copy_success = proc.returncode == 0
        
        if copy_success:
            print("✅ Successfully copied to clipboard")
            
            # Test reading from clipboard
            if os.environ.get('WAYLAND_DISPLAY'):
                result = subprocess.run(['wl-paste'], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip() == test_text:
                print("✅ Successfully read from clipboard")
                print(f"Clipboard content: '{result.stdout.strip()}'")
                return True
            else:
                print("❌ Failed to read from clipboard")
                return False
        else:
            print("❌ Failed to copy to clipboard")
            return False
            
    except Exception as e:
        print(f"❌ Clipboard test failed: {e}")
        return False

def test_window_focus():
    """Test getting current window information"""
    print_header("Testing Window Focus Detection")
    
    try:
        # Try to get current window info
        if os.environ.get('WAYLAND_DISPLAY'):
            print("🔍 Wayland detected - window detection limited")
            print("Note: Wayland has security restrictions on window detection")
        else:
            # X11 - can get more window info
            try:
                result = subprocess.run(['xdotool', 'getactivewindow'], capture_output=True, text=True)
                if result.returncode == 0:
                    window_id = result.stdout.strip()
                    print(f"✅ Active window ID: {window_id}")
                    
                    # Get window name
                    name_result = subprocess.run(['xdotool', 'getwindowname', window_id], 
                                               capture_output=True, text=True)
                    if name_result.returncode == 0:
                        print(f"✅ Active window name: '{name_result.stdout.strip()}'")
                    
                    return True
                else:
                    print("❌ Could not get active window")
                    return False
            except FileNotFoundError:
                print("❌ xdotool not found")
                return False
    except Exception as e:
        print(f"❌ Window focus test failed: {e}")
        return False

def interactive_typing_test():
    """Interactive test where user positions cursor and we type"""
    print_header("Interactive Cursor Typing Test")
    
    test_messages = [
        "Hello, this is test message 1!",
        "Testing cursor typing functionality.",
        "Can you see this text being typed?",
        "Final test message - cursor typing works!",
    ]
    
    print("🎯 This test will type text at your cursor position")
    print("📝 You'll position your cursor, then we'll type text")
    print("💬 You'll give feedback on what happened")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i}/{len(test_messages)} ---")
        print(f"Text to type: '{message}'")
        
        wait_for_user("Position your cursor where you want the text to appear")
        
        print("🎯 Typing text in 3 seconds...")
        time.sleep(1)
        print("🎯 Typing text in 2 seconds...")
        time.sleep(1)
        print("🎯 Typing text in 1 second...")
        time.sleep(1)
        print("🎯 Typing now!")
        
        # Use our cursor typing tool
        result = type_text.invoke({"text": message})
        print(f"📊 Typing result: {result}")
        
        # Get user feedback
        feedback = get_user_input("Did the text appear at your cursor? (yes/no/partial)")
        
        if feedback.lower().startswith('y'):
            print("✅ Success! Cursor typing worked")
        elif feedback.lower().startswith('p'):
            print("⚠️ Partial success - some issues detected")
            issue = get_user_input("What happened? (describe the issue)")
            print(f"📝 Issue noted: {issue}")
        else:
            print("❌ Failed - text did not appear at cursor")
            issue = get_user_input("What happened instead? (describe what you saw)")
            print(f"📝 Issue noted: {issue}")
        
        # Ask if they want to continue
        if i < len(test_messages):
            continue_test = get_user_input("Continue with next test? (yes/no)")
            if not continue_test.lower().startswith('y'):
                break

def test_paste_method():
    """Test the paste method specifically"""
    print_header("Testing Paste Method")
    
    test_text = "Testing paste method - Ctrl+V simulation!"
    
    print(f"Text to paste: '{test_text}'")
    wait_for_user("Position your cursor where you want the text to be pasted")
    
    print("📋 Pasting text in 3 seconds...")
    time.sleep(1)
    print("📋 Pasting text in 2 seconds...")
    time.sleep(1)
    print("📋 Pasting text in 1 second...")
    time.sleep(1)
    print("📋 Pasting now!")
    
    # Use paste method
    result = paste_text.invoke({"text": test_text})
    print(f"📊 Paste result: {result}")
    
    feedback = get_user_input("Did the text get pasted at your cursor? (yes/no)")
    
    if feedback.lower().startswith('y'):
        print("✅ Paste method works!")
        return True
    else:
        print("❌ Paste method failed")
        issue = get_user_input("What happened? (describe the issue)")
        print(f"📝 Issue: {issue}")
        return False

def main():
    """Main test function"""
    print("🧠 Voxtral Cursor Typing Interactive Test")
    print("=" * 60)
    print("This script will test cursor typing functionality interactively.")
    print("You'll position your cursor and give feedback on the results.")
    
    # Check system info
    print(f"\n🖥️ System Info:")
    print(f"   Display Server: {'Wayland' if os.environ.get('WAYLAND_DISPLAY') else 'X11' if os.environ.get('DISPLAY') else 'Unknown'}")
    print(f"   Desktop: {os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')}")
    
    tests = [
        ("Clipboard Functionality", test_clipboard_functionality),
        ("Window Focus Detection", test_window_focus),
        ("Interactive Typing Test", interactive_typing_test),
        ("Paste Method Test", test_paste_method),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Running: {test_name}")
            run_test = get_user_input(f"Run {test_name}? (yes/no)")
            
            if run_test.lower().startswith('y'):
                results[test_name] = test_func()
            else:
                print(f"⏭️ Skipping {test_name}")
                results[test_name] = None
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print_header("Test Summary")
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        elif result is None:
            print(f"⏭️ {test_name}: SKIPPED")
        else:
            print(f"❓ {test_name}: UNKNOWN")
    
    print(f"\n🎯 Cursor typing test completed!")
    print("📝 Based on the results, we can identify and fix any issues.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Test interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()