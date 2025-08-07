#!/usr/bin/env python3
"""
Simple hotkey test - just test Ctrl+Alt detection
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add system Python path for pynput
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.insert(0, '/usr/lib/python3/dist-packages')

try:
    from pynput import keyboard
    from pynput.keyboard import Key
    print("✅ pynput imported successfully")
except ImportError as e:
    print(f"❌ pynput import failed: {e}")
    sys.exit(1)

class SimpleHotkeyTest:
    def __init__(self):
        self.pressed_keys = set()
        self.hotkey_active = False
        
    def on_key_press(self, key):
        try:
            # Convert key to string
            if key == Key.ctrl_l or key == Key.ctrl_r:
                key_str = 'ctrl'
            elif key == Key.alt_l or key == Key.alt_r:
                key_str = 'alt'
            elif hasattr(key, 'char') and key.char:
                key_str = key.char.lower()
            else:
                key_str = str(key).lower()
            
            self.pressed_keys.add(key_str)
            
            # Check if Ctrl+Alt is pressed
            if 'ctrl' in self.pressed_keys and 'alt' in self.pressed_keys:
                if not self.hotkey_active:
                    self.hotkey_active = True
                    print("🎉 CTRL+ALT DETECTED! Hotkey is working!")
                    
        except Exception as e:
            print(f"Key press error: {e}")
    
    def on_key_release(self, key):
        try:
            # Convert key to string
            if key == Key.ctrl_l or key == Key.ctrl_r:
                key_str = 'ctrl'
            elif key == Key.alt_l or key == Key.alt_r:
                key_str = 'alt'
            elif hasattr(key, 'char') and key.char:
                key_str = key.char.lower()
            else:
                key_str = str(key).lower()
            
            self.pressed_keys.discard(key_str)
            
            # Reset hotkey when keys released
            if key_str in ['ctrl', 'alt']:
                if self.hotkey_active:
                    self.hotkey_active = False
                    print("⏹️ Ctrl+Alt released")
                    
        except Exception as e:
            print(f"Key release error: {e}")

def main():
    print("🧪 Simple Hotkey Test")
    print("=" * 30)
    print("Press Ctrl+Alt to test hotkey detection")
    print("Press Ctrl+C to exit")
    print()
    
    tester = SimpleHotkeyTest()
    
    try:
        # Start keyboard listener
        with keyboard.Listener(
            on_press=tester.on_key_press,
            on_release=tester.on_key_release
        ) as listener:
            listener.join()
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()