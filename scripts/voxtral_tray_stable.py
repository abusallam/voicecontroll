#!/usr/bin/env python3
"""
Voxtral Stable System Tray - Fixed All Issues
Addresses: tensor errors, buffer overflow, quit issues, microphone conflicts
"""

import sys
import os
import threading
import subprocess
import time
import tempfile
import signal
import gc
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Use system Python for GTK libraries
if '/usr/lib/python3/dist-packages' not in sys.path:
    sys.path.insert(0, '/usr/lib/python3/dist-packages')

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import Gtk, AyatanaAppIndicator3 as AppIndicator3, GObject, GLib
    GTK_AVAILABLE = True
except ImportError as e:
    print(f"❌ GTK not available: {e}")
    print("Please install: sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1")
    GTK_AVAILABLE = False

try:
    import whisper
    import sounddevice as sd
    import numpy as np
    import soundfile as sf
    WHISPER_AVAILABLE = True
    print("✅ All audio libraries available")
except ImportError as e:
    print(f"❌ Missing libraries: {e}")
    WHISPER_AVAILABLE = False

try:
    import pynput
    from pynput import keyboard
    HOTKEY_AVAILABLE = True
    print("✅ Global hotkey support available")
except ImportError as e:
    print(f"⚠️ Hotkey support not available: {e}")
    HOTKEY_AVAILABLE = False

class StableCursorTyping:
    """Stable cursor typing with error handling"""
    
    def __init__(self):
        self.available_tools = self._check_available_tools()
        print(f"🔧 Available typing tools: {list(self.available_tools.keys())}")
    
    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which typing tools are available"""
        tools = {}
        
        for tool in ['ydotool', 'wtype', 'xdotool', 'wl-copy', 'xclip']:
            try:
                result = subprocess.run(['which', tool], capture_output=True, timeout=2)
                tools[tool] = result.returncode == 0
            except:
                tools[tool] = False
        
        return tools
    
    def type_at_cursor(self, text: str) -> Dict[str, Any]:
        """Stable cursor typing with comprehensive error handling"""
        if not text or not text.strip():
            return {"success": False, "error": "Empty text"}
        
        text = text.strip()
        start_time = time.time()
        
        # Method 1: Fast ydotool (try without sudo first)
        if self.available_tools.get('ydotool'):
            try:
                # Try without sudo first
                result = subprocess.run(
                    ['ydotool', 'type', text], 
                    capture_output=True, 
                    text=True, 
                    timeout=2
                )
                if result.returncode == 0:
                    elapsed = (time.time() - start_time) * 1000
                    return {"success": True, "method": "ydotool_fast", "time_ms": elapsed}
                
                # Try with sudo but shorter timeout
                result = subprocess.run(
                    ['sudo', 'ydotool', 'type', text], 
                    capture_output=True, 
                    text=True, 
                    timeout=3
                )
                if result.returncode == 0:
                    elapsed = (time.time() - start_time) * 1000
                    return {"success": True, "method": "ydotool_sudo", "time_ms": elapsed}
                    
            except subprocess.TimeoutExpired:
                print("⚠️ ydotool timeout")
            except Exception as e:
                print(f"⚠️ ydotool error: {e}")
        
        # Method 2: wtype for Wayland
        if self.available_tools.get('wtype') and os.environ.get('WAYLAND_DISPLAY'):
            try:
                result = subprocess.run(
                    ['wtype', text], 
                    capture_output=True, 
                    text=True, 
                    timeout=2
                )
                if result.returncode == 0:
                    elapsed = (time.time() - start_time) * 1000
                    return {"success": True, "method": "wtype", "time_ms": elapsed}
            except Exception as e:
                print(f"⚠️ wtype error: {e}")
        
        # Method 3: Clipboard fallback (always works)
        try:
            if os.environ.get('WAYLAND_DISPLAY') and self.available_tools.get('wl-copy'):
                proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=2)
                if proc.returncode == 0:
                    elapsed = (time.time() - start_time) * 1000
                    return {
                        "success": True, 
                        "method": "clipboard_wayland", 
                        "time_ms": elapsed,
                        "message": "Text copied - press Ctrl+V to paste",
                        "fallback": True
                    }
            
            elif os.environ.get('DISPLAY') and self.available_tools.get('xclip'):
                proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                      stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=2)
                if proc.returncode == 0:
                    elapsed = (time.time() - start_time) * 1000
                    return {
                        "success": True, 
                        "method": "clipboard_x11", 
                        "time_ms": elapsed,
                        "message": "Text copied - press Ctrl+V to paste",
                        "fallback": True
                    }
        except Exception as e:
            print(f"⚠️ Clipboard error: {e}")
        
        return {"success": False, "error": "All typing methods failed"}

class VoxtralStableTray:
    def __init__(self):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK not available")
        
        self.indicator = AppIndicator3.Indicator.new(
            "voxtral-agent-stable",
            "audio-input-microphone",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Voxtral Stable Voice Agent")
        
        # Voice processing
        self.whisper_model = None
        self.is_recording = False
        self.is_continuous = False
        self.continuous_thread = None
        self.should_stop_continuous = False  # Explicit stop flag
        
        # Audio settings - more conservative
        self.sample_rate = 16000
        self.silence_threshold = 0.02  # Slightly higher to reduce false positives
        self.silence_duration = 2.0    # Longer pause before processing
        self.min_duration = 1.0        # Longer minimum to avoid tensor errors
        self.max_duration = 15.0       # Shorter max to avoid memory issues
        
        # Memory management - more conservative
        self.audio_buffer_count = 0
        self.max_buffers = 3           # Reduced from 5 to 3
        self.last_cleanup = time.time()
        self.cleanup_interval = 30     # More frequent cleanup
        
        # Autostart management
        self.autostart_enabled = self._check_autostart_status()
        
        # Stable cursor typing
        self.cursor_typing = StableCursorTyping()
        
        # Global hotkeys
        self.hotkey_enabled = False
        self.hotkey_listener = None
        
        # Shutdown flag
        self.shutting_down = False
        
        # Load Whisper model
        if WHISPER_AVAILABLE:
            threading.Thread(target=self._load_whisper, daemon=True).start()
        
        # Setup global hotkeys if available
        if HOTKEY_AVAILABLE:
            threading.Thread(target=self._setup_global_hotkeys, daemon=True).start()
        
        self.create_menu()
        
        # Status timer
        GLib.timeout_add_seconds(2, self.update_status)
        
        print("🎤 Voxtral Stable Tray started")
    
    def _load_whisper(self):
        """Load Whisper model with conservative settings"""
        try:
            print("🧠 Loading Whisper model (base for stability)...")
            # Use base model for better stability
            self.whisper_model = whisper.load_model("base")
            print("✅ Whisper base model loaded successfully")
            GLib.idle_add(self._update_status_text, "✅ Ready - Stable Model")
        except Exception as e:
            print(f"❌ Whisper loading failed: {e}")
            try:
                print("🔄 Falling back to tiny model...")
                self.whisper_model = whisper.load_model("tiny")
                print("✅ Tiny model loaded")
                GLib.idle_add(self._update_status_text, "✅ Ready - Tiny Model")
            except Exception as e2:
                print(f"❌ All models failed: {e2}")
                GLib.idle_add(self._update_status_text, "❌ Model Loading Failed")
    
    def _setup_global_hotkeys(self):
        """Setup global hotkeys for voice activation"""
        try:
            def on_hotkey():
                if not self.shutting_down:
                    print("🔥 Global hotkey activated!")
                    if not self.is_recording and not self.is_continuous:
                        GLib.idle_add(self.quick_record, None)
            
            # Register Ctrl+Alt hotkey
            hotkey = keyboard.HotKey(
                keyboard.HotKey.parse('<ctrl>+<alt>'),
                on_hotkey
            )
            
            def for_canonical(f):
                return lambda k: f(self.hotkey_listener.canonical(k))
            
            self.hotkey_listener = keyboard.Listener(
                on_press=for_canonical(hotkey.press),
                on_release=for_canonical(hotkey.release)
            )
            
            self.hotkey_listener.start()
            self.hotkey_enabled = True
            print("✅ Global hotkeys enabled (Ctrl+Alt)")
            
        except Exception as e:
            print(f"⚠️ Failed to setup global hotkeys: {e}")
    
    def create_menu(self):
        """Create stable system tray menu"""
        menu = Gtk.Menu()
        
        # Status
        self.status_item = Gtk.MenuItem(label="🧠 Loading...")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quick Record - directly in main menu
        self.quick_item = Gtk.MenuItem(label="🎙️ Quick Record (5s)")
        self.quick_item.connect("activate", self.quick_record)
        menu.append(self.quick_item)
        
        # Continuous Dictation - directly in main menu
        self.continuous_item = Gtk.MenuItem(label="🎧 Start Continuous")
        self.continuous_item.connect("activate", self.toggle_continuous)
        menu.append(self.continuous_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Services (like the old tray)
        services_submenu = Gtk.Menu()
        services_item = Gtk.MenuItem(label="🔧 Services")
        services_item.set_submenu(services_submenu)
        menu.append(services_item)
        
        # Agent folder
        agent_folder_item = Gtk.MenuItem(label="📁 Agent Folder")
        agent_folder_item.connect("activate", lambda x: self.open_folder("agent"))
        services_submenu.append(agent_folder_item)
        
        # Tools folder
        tools_folder_item = Gtk.MenuItem(label="🔧 Tools Folder")
        tools_folder_item.connect("activate", lambda x: self.open_folder("tools"))
        services_submenu.append(tools_folder_item)
        
        # Scripts folder
        scripts_folder_item = Gtk.MenuItem(label="📜 Scripts Folder")
        scripts_folder_item.connect("activate", lambda x: self.open_folder("scripts"))
        services_submenu.append(scripts_folder_item)
        
        # Project root
        project_folder_item = Gtk.MenuItem(label="🏠 Project Root")
        project_folder_item.connect("activate", lambda x: self.open_folder("."))
        services_submenu.append(project_folder_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Settings
        settings_submenu = Gtk.Menu()
        settings_item = Gtk.MenuItem(label="⚙️ Settings")
        settings_item.set_submenu(settings_submenu)
        menu.append(settings_item)
        
        # Autostart toggle
        autostart_text = "✅ Disable Autostart" if self.autostart_enabled else "🚀 Enable Autostart"
        self.autostart_item = Gtk.MenuItem(label=autostart_text)
        self.autostart_item.connect("activate", self.toggle_autostart)
        settings_submenu.append(self.autostart_item)
        
        # Hotkey status
        if self.hotkey_enabled:
            hotkey_status_item = Gtk.MenuItem(label="✅ Hotkeys: Ctrl+Alt")
            hotkey_status_item.set_sensitive(False)
            settings_submenu.append(hotkey_status_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Test
        test_item = Gtk.MenuItem(label="🧪 Test System")
        test_item.connect("activate", self.test_system)
        menu.append(test_item)
        
        # Quit - FIXED
        quit_item = Gtk.MenuItem(label="❌ Quit")
        quit_item.connect("activate", self.quit_app)
        menu.append(quit_item)
        
        menu.show_all()
        self.indicator.set_menu(menu)
    
    def quick_record(self, widget):
        """5-second quick record with stable processing"""
        if self.is_recording or not self.whisper_model or self.shutting_down:
            return
        
        self.is_recording = True
        self.quick_item.set_label("🔴 Recording...")
        
        threading.Thread(target=self._do_quick_record, daemon=True).start()
    
    def _do_quick_record(self):
        """Perform quick recording with stable transcription"""
        try:
            print("🎙️ Starting 5-second stable record...")
            
            # Record audio with exclusive access
            duration = 5
            audio_data = sd.rec(int(duration * self.sample_rate), 
                              samplerate=self.sample_rate, 
                              channels=1, 
                              dtype=np.float32)
            sd.wait()
            
            print("🧠 Transcribing with stable parameters...")
            
            # Validate audio before processing
            if len(audio_data) == 0 or np.all(audio_data == 0):
                print("⚠️ No audio data recorded")
                return
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, self.sample_rate)
                temp_path = temp_file.name
            
            try:
                # Stable transcription - no advanced parameters that cause tensor errors
                result = self.whisper_model.transcribe(
                    temp_path, 
                    language="en",
                    temperature=0.0,
                    # Removed problematic parameters: best_of, beam_size, patience
                    condition_on_previous_text=False,
                    word_timestamps=False,
                    fp16=False  # Explicitly disable FP16 to avoid warnings
                )
                transcript = result["text"].strip()
                
                if transcript:
                    print(f"📝 Transcription: {transcript}")
                    self._type_at_cursor_stable(transcript)
                else:
                    print("⚠️ No speech detected")
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"❌ Quick record error: {e}")
        finally:
            self.is_recording = False
            GLib.idle_add(self.quick_item.set_label, "🎙️ Quick Record (5s)")
    
    def toggle_continuous(self, widget):
        """Toggle continuous dictation with proper stop mechanism"""
        if not self.whisper_model or self.shutting_down:
            return
        
        if self.is_continuous:
            # Stop continuous mode
            print("⏹️ Stopping continuous dictation...")
            self.should_stop_continuous = True
            self.is_continuous = False
            self.continuous_item.set_label("🎧 Start Continuous")
        else:
            # Start continuous mode
            print("🎧 Starting continuous dictation...")
            self.should_stop_continuous = False
            self.is_continuous = True
            self.continuous_item.set_label("🔴 Stop Continuous")
            self.continuous_thread = threading.Thread(target=self._continuous_loop, daemon=True)
            self.continuous_thread.start()
    
    def _continuous_loop(self):
        """Stable continuous dictation loop"""
        print("🎙️ Continuous loop started")
        
        try:
            chunk_duration = 0.1
            chunk_samples = int(self.sample_rate * chunk_duration)
            
            is_speaking = False
            silence_start = None
            audio_buffer = []
            
            # Use audio stream without exclusive access (not supported in this version)
            with sd.InputStream(samplerate=self.sample_rate, channels=1, 
                              dtype=np.float32, blocksize=chunk_samples) as stream:
                
                while self.is_continuous and not self.should_stop_continuous and not self.shutting_down:
                    try:
                        audio_chunk, overflowed = stream.read(chunk_samples)
                        
                        if overflowed or audio_chunk is None:
                            continue
                        
                        audio_data = audio_chunk.flatten()
                        
                        # Validate audio data
                        if len(audio_data) == 0 or np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                            continue
                        
                        # Voice activity detection
                        rms_energy = np.sqrt(np.mean(audio_data ** 2))
                        has_voice = rms_energy > self.silence_threshold
                        
                        if has_voice:
                            if not is_speaking:
                                print("🎙️ Speech detected")
                                is_speaking = True
                                audio_buffer = []
                                silence_start = None
                            
                            audio_buffer.extend(audio_data)
                        else:
                            if is_speaking:
                                if silence_start is None:
                                    silence_start = time.time()
                                
                                audio_buffer.extend(audio_data)
                                
                                if time.time() - silence_start >= self.silence_duration:
                                    print("🔇 Processing speech...")
                                    
                                    if len(audio_buffer) > 0:
                                        # Check buffer limits before processing
                                        if self.audio_buffer_count < self.max_buffers:
                                            threading.Thread(
                                                target=self._process_audio_stable,
                                                args=(np.array(audio_buffer),),
                                                daemon=True
                                            ).start()
                                        else:
                                            print(f"⚠️ Buffer limit reached ({self.audio_buffer_count}), skipping")
                                    
                                    is_speaking = False
                                    silence_start = None
                                    audio_buffer = []
                        
                        time.sleep(0.01)
                        
                    except Exception as e:
                        print(f"⚠️ Audio processing error: {e}")
                        time.sleep(0.1)
                        
        except Exception as e:
            print(f"❌ Continuous loop error: {e}")
        finally:
            print("🔇 Continuous loop ended")
            self.is_continuous = False
            self.should_stop_continuous = False
            GLib.idle_add(self.continuous_item.set_label, "🎧 Start Continuous")
    
    def _process_audio_stable(self, audio_data):
        """Process audio with comprehensive error handling"""
        try:
            self.audio_buffer_count += 1
            
            # Periodic cleanup
            if time.time() - self.last_cleanup > self.cleanup_interval:
                self._cleanup_memory()
                self.last_cleanup = time.time()
            
            # Validate audio data thoroughly
            if len(audio_data) == 0:
                print("⚠️ Empty audio data")
                return
            
            # Check for invalid values
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                print("⚠️ Invalid audio values detected")
                return
            
            # Check if audio is all zeros (silence)
            if np.all(audio_data == 0):
                print("⚠️ Audio is all zeros (silence)")
                return
            
            duration = len(audio_data) / self.sample_rate
            if duration < self.min_duration:
                print(f"⚠️ Audio too short ({duration:.2f}s)")
                return
            
            if duration > self.max_duration:
                print(f"⚠️ Audio too long ({duration:.2f}s), truncating")
                max_samples = int(self.max_duration * self.sample_rate)
                audio_data = audio_data[:max_samples]
            
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            if rms_energy < 0.001:
                print(f"⚠️ Audio too quiet ({rms_energy:.6f})")
                return
            
            print(f"🧠 Processing {duration:.2f}s audio...")
            
            # Normalize audio safely
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val * 0.9  # Conservative normalization
            
            # Ensure audio data is valid after normalization
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                print("⚠️ Audio became invalid after normalization")
                return
            
            # Save and transcribe
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, self.sample_rate)
                temp_path = temp_file.name
            
            try:
                # Stable transcription without problematic parameters
                result = self.whisper_model.transcribe(
                    temp_path,
                    language="en",
                    temperature=0.0,
                    condition_on_previous_text=False,
                    word_timestamps=False,
                    fp16=False  # Explicitly disable FP16
                )
                transcript = result["text"].strip()
                
                if transcript and not self._is_garbage(transcript):
                    print(f"📝 Transcription: {transcript}")
                    self._type_at_cursor_stable(transcript)
                else:
                    print("⚠️ No valid speech detected")
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"❌ Audio processing error: {e}")
            # Don't crash, just log and continue
        finally:
            self.audio_buffer_count -= 1
    
    def _is_garbage(self, text):
        """Check if transcription is garbage"""
        if not text or len(text.strip()) < 2:
            return True
        
        text_lower = text.lower().strip()
        garbage_patterns = [
            "one biased", "dictation", "biased", "you", "thank you",
            "uh", "um", "ah", "hmm", "mm", "yeah", "yes", "no",
            ".", "?", "!", ",", "okay", "ok"
        ]
        
        return text_lower in garbage_patterns
    
    def _type_at_cursor_stable(self, text):
        """Stable cursor typing with comprehensive error handling"""
        try:
            result = self.cursor_typing.type_at_cursor(text)
            
            if result["success"]:
                time_ms = result.get("time_ms", 0)
                if result.get("fallback"):
                    print(f"📋 {result.get('message', 'Text ready in clipboard')} ({time_ms:.0f}ms)")
                else:
                    print(f"✅ Typed using {result['method']} ({time_ms:.0f}ms)")
            else:
                print(f"⚠️ Typing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Stable cursor typing error: {e}")
    
    def open_folder(self, folder_name):
        """Open project folder in file manager"""
        try:
            folder_path = project_root / folder_name
            if folder_path.exists():
                subprocess.Popen(["xdg-open", str(folder_path)])
                print(f"📁 Opened {folder_name} folder")
            else:
                print(f"⚠️ Folder {folder_name} not found")
        except Exception as e:
            print(f"❌ Failed to open folder {folder_name}: {e}")
    
    def _cleanup_memory(self):
        """Enhanced memory cleanup"""
        try:
            print("🧹 Enhanced memory cleanup...")
            
            # Force garbage collection
            gc.collect()
            
            # Reset buffer count if it's stuck
            if self.audio_buffer_count > 0:
                print(f"🔧 Resetting buffer count from {self.audio_buffer_count} to 0")
                self.audio_buffer_count = 0
            
            print("✅ Enhanced cleanup complete")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    def _check_autostart_status(self):
        """Check if autostart is currently enabled"""
        try:
            # Check systemd service
            result = subprocess.run(
                ['systemctl', '--user', 'is-enabled', 'voxtral-tray.service'],
                capture_output=True, text=True, timeout=5
            )
            systemd_enabled = result.returncode == 0 and result.stdout.strip() == 'enabled'
            
            # Check desktop autostart
            desktop_file = Path.home() / ".config/autostart/voxtral-tray.desktop"
            desktop_enabled = desktop_file.exists()
            
            return systemd_enabled or desktop_enabled
            
        except Exception as e:
            print(f"⚠️ Error checking autostart status: {e}")
            return False
    
    def _toggle_autostart(self):
        """Toggle autostart functionality"""
        try:
            if self.autostart_enabled:
                # Disable autostart
                success = self._disable_autostart()
                if success:
                    self.autostart_enabled = False
                    print("✅ Autostart disabled")
                    GLib.idle_add(self._update_autostart_menu)
                else:
                    print("❌ Failed to disable autostart")
            else:
                # Enable autostart
                success = self._enable_autostart()
                if success:
                    self.autostart_enabled = True
                    print("✅ Autostart enabled")
                    GLib.idle_add(self._update_autostart_menu)
                else:
                    print("❌ Failed to enable autostart")
                    
        except Exception as e:
            print(f"❌ Error toggling autostart: {e}")
    
    def _enable_autostart(self):
        """Enable autostart using systemd (preferred method)"""
        try:
            # Run the setup script
            setup_script = project_root / "scripts/setup_autostart.sh"
            if setup_script.exists():
                result = subprocess.run(
                    ['bash', str(setup_script)],
                    input='n\n',  # Don't start service now
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0
            else:
                # Fallback: create systemd service manually
                return self._create_systemd_service()
                
        except Exception as e:
            print(f"❌ Error enabling autostart: {e}")
            return False
    
    def _disable_autostart(self):
        """Disable all autostart methods"""
        try:
            success = True
            
            # Disable systemd service
            try:
                subprocess.run(['systemctl', '--user', 'disable', 'voxtral-tray.service'], 
                             check=True, capture_output=True, timeout=10)
                subprocess.run(['systemctl', '--user', 'stop', 'voxtral-tray.service'], 
                             capture_output=True, timeout=10)  # Don't fail if not running
            except subprocess.CalledProcessError:
                pass  # Service might not exist
            except subprocess.TimeoutExpired:
                print("⚠️ Systemd command timeout")
            
            # Remove desktop autostart file
            desktop_file = Path.home() / ".config/autostart/voxtral-tray.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
            
            return success
            
        except Exception as e:
            print(f"❌ Error disabling autostart: {e}")
            return False
    
    def _create_systemd_service(self):
        """Create systemd service manually"""
        try:
            systemd_dir = Path.home() / ".config/systemd/user"
            systemd_dir.mkdir(parents=True, exist_ok=True)
            
            service_file = systemd_dir / "voxtral-tray.service"
            python_path = project_root / ".venv/bin/python"
            script_path = project_root / "scripts/voxtral_tray_stable.py"
            
            service_content = f"""[Unit]
Description=Voxtral Stable Voice Platform Tray
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Restart=always
RestartSec=5
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=%i
ExecStart={python_path} {script_path}
WorkingDirectory={project_root}

# Ensure the service starts after the desktop environment is ready
ExecStartPre=/bin/sleep 10

[Install]
WantedBy=default.target
"""
            
            service_file.write_text(service_content)
            
            # Enable the service
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True, timeout=10)
            subprocess.run(['systemctl', '--user', 'enable', 'voxtral-tray.service'], check=True, timeout=10)
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating systemd service: {e}")
            return False
    
    def toggle_autostart(self, widget):
        """Toggle autostart from menu"""
        threading.Thread(target=self._toggle_autostart, daemon=True).start()
    
    def _update_autostart_menu(self):
        """Update autostart menu item text"""
        try:
            autostart_text = "✅ Disable Autostart" if self.autostart_enabled else "🚀 Enable Autostart"
            self.autostart_item.set_label(autostart_text)
        except Exception as e:
            print(f"⚠️ Error updating autostart menu: {e}")
    
    def test_system(self, widget):
        """Run system test"""
        try:
            subprocess.Popen([
                "gnome-terminal", "--", "bash", "-c",
                f"cd {project_root} && uv run scripts/test_system.py; read -p 'Press Enter...'"
            ])
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    def update_status(self):
        """Update status"""
        if self.shutting_down:
            return False
        
        try:
            if self.whisper_model:
                if self.is_continuous:
                    status = "🔴 Listening..."
                elif self.is_recording:
                    status = "🎙️ Recording..."
                else:
                    status = "✅ Ready - Stable"
                    if self.hotkey_enabled:
                        status += " + ⌨️"
            else:
                status = "🧠 Loading..."
            
            self.status_item.set_label(status)
            
            # Update menu sensitivity
            ready = self.whisper_model is not None and not self.shutting_down
            self.quick_item.set_sensitive(ready and not self.is_recording and not self.is_continuous)
            self.continuous_item.set_sensitive(ready)
            
        except Exception as e:
            print(f"⚠️ Status update error: {e}")
        
        return True
    
    def _update_status_text(self, text):
        """Update status text safely"""
        if self.shutting_down:
            return
        
        try:
            self.status_item.set_label(text)
        except Exception as e:
            print(f"⚠️ Status text error: {e}")
    
    def quit_app(self, widget):
        """Nuclear quit - kill process immediately"""
        print("🔥 NUCLEAR SHUTDOWN - KILLING PROCESS")
        
        # Kill the process immediately using subprocess
        import subprocess
        import os
        
        try:
            # Get current process ID
            pid = os.getpid()
            print(f"🔥 Killing PID: {pid}")
            
            # Kill ourselves
            subprocess.run(['kill', '-9', str(pid)])
        except:
            # If that fails, force exit
            os._exit(1)

def main():
    """Main entry point"""
    try:
        if not GTK_AVAILABLE:
            print("❌ GTK not available")
            return 1
        
        app = VoxtralStableTray()
        
        def signal_handler(signum, frame):
            print(f"\\n🛑 Signal {signum} received")
            app.quit_app(None)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        Gtk.main()
        return 0
        
    except KeyboardInterrupt:
        print("\\n🛑 Interrupted")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())