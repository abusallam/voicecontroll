#!/usr/bin/env python3
"""
Global Hotkey Manager for Voxtral Agent
Implements Ctrl+Alt hotkey activation for voice transcription
"""

import sys
import os
import threading
import time
import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add system Python path for pynput
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.insert(0, '/usr/lib/python3/dist-packages')

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    PYNPUT_AVAILABLE = True
except ImportError as e:
    print(f"❌ pynput not available: {e}")
    print("Install with: sudo apt install python3-pynput")
    PYNPUT_AVAILABLE = False

from config.settings import config

@dataclass
class HotkeyConfig:
    """Configuration for hotkey behavior"""
    keys: list
    enabled: bool
    feedback_type: str  # 'visual', 'audio', 'both', 'none'
    toggle_mode: bool   # True for toggle, False for push-to-talk

class HotkeyManager:
    """Manages global hotkeys for voice activation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.listener = None
        self.is_listening = False
        self.voice_active = False
        self.pressed_keys = set()
        
        # Load configuration
        self.config = self._load_hotkey_config()
        
        # Callbacks
        self.activation_callback = None
        self.deactivation_callback = None
        self.status_callback = None
        
        # Thread safety
        self.lock = threading.Lock()
        
    def _load_hotkey_config(self) -> HotkeyConfig:
        """Load hotkey configuration from settings"""
        hotkey_config = config.get("hotkeys", {})
        
        return HotkeyConfig(
            keys=hotkey_config.get("activation_keys", ["ctrl", "alt"]),
            enabled=hotkey_config.get("enabled", True),
            feedback_type=hotkey_config.get("feedback", {}).get("type", "visual"),
            toggle_mode=hotkey_config.get("toggle_mode", True)
        )
    
    def set_activation_callback(self, callback: Callable[[], None]):
        """Set callback for voice activation"""
        self.activation_callback = callback
    
    def set_deactivation_callback(self, callback: Callable[[], None]):
        """Set callback for voice deactivation"""
        self.deactivation_callback = callback
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def register_hotkey(self) -> bool:
        """Register the global hotkey"""
        if not PYNPUT_AVAILABLE:
            self.logger.error("pynput not available, cannot register hotkeys")
            return False
        
        if not self.config.enabled:
            self.logger.info("Hotkeys disabled in configuration")
            return False
        
        try:
            self.logger.info(f"Registering hotkey: {'+'.join(self.config.keys)}")
            
            # Start the keyboard listener
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            self.listener.start()
            self.is_listening = True
            
            self.logger.info("✅ Global hotkey registered successfully")
            self._notify_status("Hotkey registered: Ctrl+Alt")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register hotkey: {e}")
            return False
    
    def unregister_hotkey(self) -> bool:
        """Unregister the global hotkey"""
        try:
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            self.is_listening = False
            self.pressed_keys.clear()
            
            self.logger.info("Hotkey unregistered")
            self._notify_status("Hotkey unregistered")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister hotkey: {e}")
            return False
    
    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            with self.lock:
                # Convert key to string representation
                key_str = self._key_to_string(key)
                if key_str:
                    self.pressed_keys.add(key_str)
                    
                    # Check if our hotkey combination is pressed
                    if self._is_hotkey_pressed():
                        self._handle_hotkey_activation()
                        
        except Exception as e:
            self.logger.error(f"Key press error: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events"""
        try:
            with self.lock:
                key_str = self._key_to_string(key)
                if key_str:
                    self.pressed_keys.discard(key_str)
                    
                    # Handle push-to-talk mode
                    if not self.config.toggle_mode and not self._is_hotkey_pressed():
                        if self.voice_active:
                            self._handle_hotkey_deactivation()
                            
        except Exception as e:
            self.logger.error(f"Key release error: {e}")
    
    def _key_to_string(self, key) -> Optional[str]:
        """Convert pynput key to string"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            elif key == Key.ctrl_l or key == Key.ctrl_r:
                return 'ctrl'
            elif key == Key.alt_l or key == Key.alt_r:
                return 'alt'
            elif key == Key.shift_l or key == Key.shift_r:
                return 'shift'
            elif key == Key.cmd:
                return 'cmd'
            elif hasattr(key, 'name'):
                return key.name.lower()
            else:
                return str(key).lower()
        except:
            return None
    
    def _is_hotkey_pressed(self) -> bool:
        """Check if the configured hotkey combination is pressed"""
        required_keys = set(key.lower() for key in self.config.keys)
        return required_keys.issubset(self.pressed_keys)
    
    def _handle_hotkey_activation(self):
        """Handle hotkey activation"""
        try:
            if self.config.toggle_mode:
                # Toggle mode: switch between active/inactive
                if self.voice_active:
                    self._handle_hotkey_deactivation()
                else:
                    self._activate_voice()
            else:
                # Push-to-talk mode: activate while held
                if not self.voice_active:
                    self._activate_voice()
                    
        except Exception as e:
            self.logger.error(f"Hotkey activation error: {e}")
    
    def _handle_hotkey_deactivation(self):
        """Handle hotkey deactivation"""
        try:
            self._deactivate_voice()
        except Exception as e:
            self.logger.error(f"Hotkey deactivation error: {e}")
    
    def _activate_voice(self):
        """Activate voice transcription"""
        if self.voice_active:
            return
            
        self.voice_active = True
        self.logger.info("🎙️ Voice activated by hotkey")
        
        # Provide feedback
        self._provide_feedback("activated")
        
        # Call activation callback
        if self.activation_callback:
            try:
                threading.Thread(target=self.activation_callback, daemon=True).start()
            except Exception as e:
                self.logger.error(f"Activation callback error: {e}")
        
        self._notify_status("Voice activated")
    
    def _deactivate_voice(self):
        """Deactivate voice transcription"""
        if not self.voice_active:
            return
            
        self.voice_active = False
        self.logger.info("⏹️ Voice deactivated by hotkey")
        
        # Provide feedback
        self._provide_feedback("deactivated")
        
        # Call deactivation callback
        if self.deactivation_callback:
            try:
                threading.Thread(target=self.deactivation_callback, daemon=True).start()
            except Exception as e:
                self.logger.error(f"Deactivation callback error: {e}")
        
        self._notify_status("Voice deactivated")
    
    def _provide_feedback(self, action: str):
        """Provide user feedback for hotkey actions"""
        feedback_type = self.config.feedback_type
        
        if feedback_type in ["visual", "both"]:
            self._provide_visual_feedback(action)
        
        if feedback_type in ["audio", "both"]:
            self._provide_audio_feedback(action)
    
    def _provide_visual_feedback(self, action: str):
        """Provide visual feedback (notification)"""
        try:
            import subprocess
            
            if action == "activated":
                title = "🎙️ Voice Activated"
                message = "Listening for speech..."
                icon = "audio-input-microphone"
            else:
                title = "⏹️ Voice Deactivated"
                message = "Stopped listening"
                icon = "audio-input-microphone-muted"
            
            # Try to show desktop notification
            subprocess.run([
                'notify-send', 
                '--icon', icon,
                '--expire-time', '2000',
                title, message
            ], capture_output=True, timeout=2)
            
        except Exception as e:
            self.logger.debug(f"Visual feedback error: {e}")
    
    def _provide_audio_feedback(self, action: str):
        """Provide audio feedback (system sound)"""
        try:
            import subprocess
            
            if action == "activated":
                sound_file = "/usr/share/sounds/alsa/Front_Left.wav"
            else:
                sound_file = "/usr/share/sounds/alsa/Front_Right.wav"
            
            # Try to play system sound
            subprocess.run(['paplay', sound_file], 
                         capture_output=True, timeout=2)
            
        except Exception as e:
            self.logger.debug(f"Audio feedback error: {e}")
    
    def _notify_status(self, status: str):
        """Notify status callback"""
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get hotkey manager status"""
        return {
            "enabled": self.config.enabled,
            "listening": self.is_listening,
            "voice_active": self.voice_active,
            "hotkey": "+".join(self.config.keys),
            "toggle_mode": self.config.toggle_mode,
            "feedback_type": self.config.feedback_type,
            "pynput_available": PYNPUT_AVAILABLE
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update hotkey configuration"""
        try:
            # Stop current listener
            if self.is_listening:
                self.unregister_hotkey()
            
            # Update configuration
            hotkey_section = config.get("hotkeys", {})
            hotkey_section.update(new_config)
            config.set("hotkeys", hotkey_section)
            config.save_config()
            
            # Reload configuration
            self.config = self._load_hotkey_config()
            
            # Restart listener if enabled
            if self.config.enabled:
                return self.register_hotkey()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Config update error: {e}")
            return False

def main():
    """Main function for testing hotkey manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Voxtral Hotkey Manager")
    parser.add_argument("--test", action="store_true", help="Test hotkey functionality")
    parser.add_argument("--status", action="store_true", help="Show hotkey status")
    parser.add_argument("--enable", action="store_true", help="Enable hotkeys")
    parser.add_argument("--disable", action="store_true", help="Disable hotkeys")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = HotkeyManager()
    
    if args.status:
        status = manager.get_status()
        print("=== Hotkey Manager Status ===")
        print(f"Enabled: {status['enabled']}")
        print(f"Listening: {status['listening']}")
        print(f"Voice Active: {status['voice_active']}")
        print(f"Hotkey: {status['hotkey']}")
        print(f"Toggle Mode: {status['toggle_mode']}")
        print(f"Feedback: {status['feedback_type']}")
        print(f"pynput Available: {status['pynput_available']}")
    
    elif args.enable:
        success = manager.update_config({"enabled": True})
        print("Enable hotkeys:", "SUCCESS" if success else "FAILED")
    
    elif args.disable:
        success = manager.update_config({"enabled": False})
        print("Disable hotkeys:", "SUCCESS" if success else "FAILED")
    
    elif args.test:
        print("🧪 Testing hotkey functionality...")
        print("Press Ctrl+Alt to test voice activation")
        print("Press Ctrl+C to exit")
        
        def test_activation():
            print("✅ Voice activation triggered!")
        
        def test_deactivation():
            print("⏹️ Voice deactivation triggered!")
        
        def test_status(status):
            print(f"📊 Status: {status}")
        
        manager.set_activation_callback(test_activation)
        manager.set_deactivation_callback(test_deactivation)
        manager.set_status_callback(test_status)
        
        if manager.register_hotkey():
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping hotkey test...")
                manager.unregister_hotkey()
        else:
            print("❌ Failed to register hotkey")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()