#!/usr/bin/env python3
"""
Voxtral GTK System Tray - Enhanced with features from previous voice-control system
Better integration with GNOME/Wayland using GTK and AppIndicator3
Uses system GTK libraries for better compatibility
"""

import sys
import os

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
import threading
import subprocess
import time
import os
import sys
import tempfile
import signal
import psutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config

# Try to import Whisper for fallback
try:
    import whisper
    import sounddevice as sd
    import numpy as np
    import soundfile as sf
    WHISPER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Whisper not available: {e}")
    WHISPER_AVAILABLE = False

class VoxtralTrayGTK:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "voxtral-agent",
            "audio-input-microphone",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Voxtral Voice Agent")
        
        # Process management
        self.agent_process = None
        self.vllm_process = None
        self.mock_server_process = None
        
        # Target window for typing
        self.target_window = None
        self.target_window_name = "None selected"
        
        # Voice recognition for quick record and continuous dictation
        self.whisper_model = None
        self.is_recording = False
        self.is_quick_recording = False
        self.is_continuous_listening = False
        self.continuous_thread = None
        
        # Voice activity detection for continuous mode
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.silence_threshold = 0.015  # More sensitive to detect actual silence
        self.silence_duration = 1.5  # Reduced to 1.5 seconds for faster response
        self.min_recording_duration = 0.8  # Reduced minimum duration
        self.max_recording_duration = 15.0  # Maximum recording duration to prevent runaway
        
        # Load Whisper model in background for quick record
        if WHISPER_AVAILABLE:
            threading.Thread(target=self._load_whisper_model, daemon=True).start()
        
        # Create menu
        self.create_menu()
        
        # Setup status update timer
        GLib.timeout_add_seconds(2, self.update_status)
        
        print("🎤 Voxtral GTK Tray started")
    
    def _load_whisper_model(self):
        """Load Whisper model in background for quick record feature"""
        try:
            print("🧠 Loading Whisper model for quick record...")
            self.whisper_model = whisper.load_model("base")
            print("✅ Whisper model loaded")
            
            # Update menu to show ready status
            GLib.idle_add(self.update_menu_status, "✅ Ready for Quick Record")
        except Exception as e:
            print(f"❌ Failed to load Whisper: {e}")
            GLib.idle_add(self.update_menu_status, "❌ Quick Record Unavailable")
    
    def create_menu(self):
        """Create the system tray menu"""
        menu = Gtk.Menu()
        
        # Status item
        self.status_item = Gtk.MenuItem(label="🧠 Initializing...")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        # Separator
        separator1 = Gtk.SeparatorMenuItem()
        menu.append(separator1)
        
        # Quick Record (5 seconds) - Feature from previous system
        self.quick_record_item = Gtk.MenuItem(label="🎙️ Quick Record (5s)")
        self.quick_record_item.connect("activate", self.quick_record)
        menu.append(self.quick_record_item)
        
        # Continuous Dictation - New feature you requested
        self.continuous_item = Gtk.MenuItem(label="🎧 Start Continuous Dictation")
        self.continuous_item.connect("activate", self.toggle_continuous_dictation)
        menu.append(self.continuous_item)
        
        # Separator
        separator2 = Gtk.SeparatorMenuItem()
        menu.append(separator2)
        
        # Agent Control
        self.start_agent_item = Gtk.MenuItem(label="🚀 Start Agent")
        self.start_agent_item.connect("activate", self.start_agent)
        menu.append(self.start_agent_item)
        
        self.stop_agent_item = Gtk.MenuItem(label="⏹️ Stop Agent")
        self.stop_agent_item.connect("activate", self.stop_agent)
        menu.append(self.stop_agent_item)
        
        self.restart_agent_item = Gtk.MenuItem(label="🔄 Restart Agent")
        self.restart_agent_item.connect("activate", self.restart_agent)
        menu.append(self.restart_agent_item)
        
        # Separator
        separator3 = Gtk.SeparatorMenuItem()
        menu.append(separator3)
        
        # VLLM Server Control
        self.start_vllm_item = Gtk.MenuItem(label="🧠 Start VLLM Server")
        self.start_vllm_item.connect("activate", self.start_vllm_server)
        menu.append(self.start_vllm_item)
        
        self.stop_vllm_item = Gtk.MenuItem(label="⏹️ Stop VLLM Server")
        self.stop_vllm_item.connect("activate", self.stop_vllm_server)
        menu.append(self.stop_vllm_item)
        
        # Separator
        separator4 = Gtk.SeparatorMenuItem()
        menu.append(separator4)
        
        # Folder access
        open_project_item = Gtk.MenuItem(label="📁 Open Project Folder")
        open_project_item.connect("activate", lambda x: self.open_folder(str(project_root)))
        menu.append(open_project_item)
        
        open_logs_item = Gtk.MenuItem(label="📋 Open Logs")
        open_logs_item.connect("activate", self.open_logs)
        menu.append(open_logs_item)
        
        open_config_item = Gtk.MenuItem(label="⚙️ Open Configuration")
        open_config_item.connect("activate", self.open_config)
        menu.append(open_config_item)
        
        # Separator
        separator5 = Gtk.SeparatorMenuItem()
        menu.append(separator5)
        
        # Test system
        test_system_item = Gtk.MenuItem(label="🧪 Test System")
        test_system_item.connect("activate", self.test_system)
        menu.append(test_system_item)
        
        # Quit
        quit_item = Gtk.MenuItem(label="❌ Quit")
        quit_item.connect("activate", self.quit_application)
        menu.append(quit_item)
        
        menu.show_all()
        self.indicator.set_menu(menu)
    
    def quick_record(self, widget):
        """Quick 5-second voice recording with immediate transcription"""
        if self.is_quick_recording:
            return
        
        if not WHISPER_AVAILABLE or not self.whisper_model:
            self.show_notification("❌ Quick Record", "Whisper model not available")
            return
        
        self.is_quick_recording = True
        self.quick_record_item.set_label("🔴 Recording... (5s)")
        
        # Start recording in background thread
        threading.Thread(target=self._do_quick_record, daemon=True).start()
    
    def _do_quick_record(self):
        """Perform the actual quick recording"""
        try:
            print("🎙️ Starting 5-second quick record...")
            
            # Record for 5 seconds
            sample_rate = 16000
            duration = 5
            
            audio_data = sd.rec(int(duration * sample_rate), 
                              samplerate=sample_rate, 
                              channels=1, 
                              dtype=np.float32)
            sd.wait()
            
            print("🧠 Transcribing audio...")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, sample_rate)
                temp_path = temp_file.name
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(temp_path, language="en")
            transcript = result["text"].strip()
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if transcript:
                print(f"📝 Transcription: {transcript}")
                
                # Type the text using our cursor typing tool
                self._type_text_at_cursor(transcript)
                
                print(f"✅ Quick Record typed: {transcript[:50]}...")
            else:
                print("⚠️ Quick Record: No speech detected")
                
        except Exception as e:
            print(f"❌ Quick record error: {e}")
            GLib.idle_add(self.show_notification, "❌ Quick Record", f"Error: {str(e)}")
        finally:
            self.is_quick_recording = False
            GLib.idle_add(self.quick_record_item.set_label, "🎙️ Quick Record (5s)")
    
    def toggle_continuous_dictation(self, widget):
        """Toggle continuous dictation mode"""
        if not WHISPER_AVAILABLE or not self.whisper_model:
            self.show_notification("❌ Continuous Dictation", "Whisper model not available")
            return
        
        if self.is_continuous_listening:
            # Stop continuous listening
            self.is_continuous_listening = False
            self.continuous_item.set_label("🎧 Start Continuous Dictation")
            self.show_notification("⏹️ Continuous Dictation", "Stopped listening")
            print("⏹️ Stopping continuous dictation...")
        else:
            # Start continuous listening
            self.is_continuous_listening = True
            self.continuous_item.set_label("🔴 Stop Continuous Dictation")
            self.show_notification("🎧 Continuous Dictation", "Started listening - speak naturally")
            print("🎧 Starting continuous dictation...")
            
            # Start continuous listening in background thread
            self.continuous_thread = threading.Thread(target=self._continuous_dictation_loop, daemon=True)
            self.continuous_thread.start()
    
    def _continuous_dictation_loop(self):
        """Main loop for continuous dictation with voice activity detection"""
        print("🎙️ Continuous dictation loop started")
        
        try:
            # Use energy-based detection only for better stability
            # WebRTC VAD has frame size issues with our audio stream
            vad_available = False
            print("🔊 Using energy-based voice detection for stability")
            
            # Audio recording parameters
            chunk_duration = 0.1  # 100ms chunks for better stability
            chunk_samples = int(self.sample_rate * chunk_duration)
            
            # State tracking
            is_speaking = False
            silence_start = None
            audio_buffer = []
            speech_frames = 0
            silence_frames = 0
            
            print("🎧 Listening for speech... (speak naturally)")
            print(f"🔧 Using {chunk_duration}s chunks, {self.silence_duration}s silence threshold")
            
            # Start audio stream with error handling
            try:
                with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype=np.float32, 
                                  blocksize=chunk_samples) as stream:
                    
                    while self.is_continuous_listening:
                        try:
                            # Read audio chunk with timeout
                            audio_chunk, overflowed = stream.read(chunk_samples)
                            
                            if overflowed:
                                print("⚠️ Audio buffer overflow")
                                continue
                            
                            # Validate audio chunk
                            if audio_chunk is None or audio_chunk.size == 0:
                                print("⚠️ Empty audio chunk received")
                                continue
                            
                            # Flatten audio data and validate
                            audio_data = audio_chunk.flatten()
                            
                            # Check for invalid audio data
                            if len(audio_data) == 0:
                                print("⚠️ Empty audio data after flattening")
                                continue
                            
                            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                                print("⚠️ Invalid audio data (NaN/Inf) in stream")
                                continue
                            
                            # Voice activity detection
                            has_voice = self._detect_voice_activity(audio_data, vad if vad_available else None)
                            
                            if has_voice:
                                speech_frames += 1
                                silence_frames = 0
                                
                                if not is_speaking:
                                    print("🎙️ Speech detected, starting recording...")
                                    is_speaking = True
                                    audio_buffer = []
                                    silence_start = None  # Reset silence timer when starting new speech
                                
                                # Add to buffer
                                audio_buffer.extend(audio_data)
                                
                            else:
                                silence_frames += 1
                                
                                if is_speaking:
                                    # We were speaking, now silence
                                    if silence_start is None:
                                        silence_start = time.time()
                                        print(f"🔇 Silence started after {speech_frames} speech frames")
                                    
                                    # Continue adding to buffer during short silence
                                    audio_buffer.extend(audio_data)
                                    
                                    # Check if silence duration exceeded threshold
                                    silence_duration = time.time() - silence_start
                                    if silence_duration >= self.silence_duration:
                                        print(f"🔇 Processing speech after {silence_duration:.1f}s silence...")
                                        
                                        # Process the recorded audio
                                        if len(audio_buffer) > 0:
                                            # Process in separate thread to avoid blocking
                                            threading.Thread(
                                                target=self._process_continuous_audio, 
                                                args=(np.array(audio_buffer),), 
                                                daemon=True
                                            ).start()
                                        
                                        # Reset state for next speech
                                        is_speaking = False
                                        silence_start = None
                                        audio_buffer = []
                                        speech_frames = 0
                                        silence_frames = 0
                                        print("🎧 Ready for next speech...")
                            
                            # Small delay to prevent excessive CPU usage
                            time.sleep(0.01)
                            
                        except Exception as e:
                            print(f"⚠️ Audio processing error: {e}")
                            time.sleep(0.1)  # Brief pause on error
                            continue
                            
            except Exception as e:
                print(f"❌ Audio stream error: {e}")
                GLib.idle_add(self.show_notification, "❌ Audio Error", f"Stream error: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Continuous dictation error: {e}")
            import traceback
            traceback.print_exc()
            GLib.idle_add(self.show_notification, "❌ Continuous Dictation", f"Error: {str(e)}")
        finally:
            print("🔇 Continuous dictation loop ended")
            self.is_continuous_listening = False
            GLib.idle_add(self.continuous_item.set_label, "🎧 Start Continuous Dictation")
    
    def _detect_voice_activity(self, audio_data: np.ndarray, vad=None) -> bool:
        """Detect voice activity in audio chunk"""
        try:
            # Validate input data first
            if audio_data is None or len(audio_data) == 0:
                return False
            
            # Check for invalid values
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                return False
            
            # Energy-based detection (always available)
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            energy_threshold = rms_energy > self.silence_threshold
            
            # WebRTC VAD detection (if available)
            if vad is not None:
                try:
                    # Ensure we have the right amount of data for VAD
                    # WebRTC VAD expects specific frame sizes (10, 20, or 30ms)
                    expected_samples = int(self.sample_rate * 0.1)  # 100ms = 0.1s
                    
                    if len(audio_data) != expected_samples:
                        # Pad or truncate to expected size
                        if len(audio_data) < expected_samples:
                            padded_data = np.pad(audio_data, (0, expected_samples - len(audio_data)), 'constant')
                        else:
                            padded_data = audio_data[:expected_samples]
                    else:
                        padded_data = audio_data
                    
                    # Convert to 16-bit PCM for WebRTC VAD with bounds checking
                    # Clamp values to prevent overflow
                    clamped_data = np.clip(padded_data, -1.0, 1.0)
                    pcm_data = (clamped_data * 32767).astype(np.int16).tobytes()
                    
                    # Verify PCM data size
                    expected_bytes = expected_samples * 2  # 2 bytes per 16-bit sample
                    if len(pcm_data) != expected_bytes:
                        print(f"⚠️ PCM data size mismatch: got {len(pcm_data)}, expected {expected_bytes}")
                        return energy_threshold
                    
                    vad_result = vad.is_speech(pcm_data, self.sample_rate)
                    
                    # Combine both methods - require both for more accuracy
                    return vad_result and energy_threshold
                    
                except Exception as vad_error:
                    print(f"⚠️ WebRTC VAD error: {vad_error}")
                    # Fall back to energy-based detection
                    return energy_threshold
            
            return energy_threshold
            
        except Exception as e:
            print(f"⚠️ VAD error: {e}")
            return False
    
    def _process_continuous_audio(self, audio_data: np.ndarray):
        """Process recorded audio from continuous dictation"""
        try:
            # Validate audio data first
            if audio_data is None or len(audio_data) == 0:
                print("⚠️ Empty audio data, skipping")
                return
            
            # Check for NaN or infinite values
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                print("⚠️ Invalid audio data (NaN/Inf), skipping")
                return
            
            # Check minimum duration
            duration = len(audio_data) / self.sample_rate
            if duration < self.min_recording_duration:
                print(f"⚠️ Recording too short ({duration:.2f}s), ignoring")
                return
            
            # Check if audio has sufficient energy
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            if rms_energy < 0.001:  # Very quiet audio
                print(f"⚠️ Audio too quiet (RMS: {rms_energy:.6f}), likely silence")
                return
            
            # Check for minimum samples to prevent tensor reshape errors
            min_samples = int(self.sample_rate * 0.1)  # At least 0.1 seconds
            if len(audio_data) < min_samples:
                print(f"⚠️ Audio too short ({len(audio_data)} samples), need at least {min_samples}")
                return
            
            print(f"🧠 Processing {duration:.2f}s of audio...")
            
            # Normalize audio to prevent clipping
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val * 0.95
            
            # Save to temporary file with error handling
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    sf.write(temp_file.name, audio_data, self.sample_rate)
                    temp_path = temp_file.name
                
                # Verify the file was written correctly
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    print("⚠️ Failed to write audio file")
                    return
                
                # Transcribe with Whisper with additional error handling
                try:
                    result = self.whisper_model.transcribe(temp_path, language="en")
                    transcript = result["text"].strip()
                except Exception as whisper_error:
                    print(f"❌ Whisper transcription error: {whisper_error}")
                    return
                
            finally:
                # Clean up temp file
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass  # Ignore cleanup errors
            
            if transcript:
                # Filter out garbage transcriptions
                if self._is_garbage_transcription(transcript):
                    print(f"🗑️ Filtered garbage transcription: {transcript}")
                    return
                
                print(f"📝 Transcription: {transcript}")
                
                # Type the text at cursor position using the improved cursor typing tool
                from tools.cursor_typing import type_text
                result = type_text.invoke({"text": transcript})
                print(f"🎯 Cursor typing result: {result}")
                
                # If text is ready to paste, show a helpful notification
                if "ready to paste" in result:
                    # Show a brief notification to remind user to paste
                    GLib.idle_add(self.show_notification, "📋 Ready to Paste", f"Press Ctrl+V to paste: {transcript[:30]}...")
                    
                    # Also try to make a brief sound notification if available
                    try:
                        subprocess.run(['paplay', '/usr/share/sounds/alsa/Front_Left.wav'], 
                                     capture_output=True, timeout=1)
                    except:
                        pass  # Sound notification is optional
                
                # Don't show notification to reduce noise - just print success
                print(f"✅ Typed at cursor: {transcript[:50]}...")
            else:
                print("⚠️ No speech detected in audio")
                
        except Exception as e:
            print(f"❌ Audio processing error: {e}")
            GLib.idle_add(self.show_notification, "❌ Dictation", f"Processing error: {str(e)}")
    
    def _is_garbage_transcription(self, text: str) -> bool:
        """Check if transcription is likely garbage/noise"""
        if not text or len(text.strip()) < 2:
            return True
            
        text_lower = text.lower().strip()
        
        # Common garbage patterns from Whisper
        garbage_patterns = [
            "one biased", "dictation", "biased", "typed text posted",
            "clipboard", "ordering", "you", "thank you", "thanks",
            "uh", "um", "ah", "hmm", "mm", "mhm", "yeah", "yes", "no",
            ".", "?", "!", ",", "...", "okay", "ok", "right", "well"
        ]
        
        # Check if the entire text is just garbage
        for pattern in garbage_patterns:
            if text_lower == pattern or text_lower.replace(" ", "") == pattern.replace(" ", ""):
                return True
        
        # Check for very repetitive text (same word repeated)
        words = text_lower.split()
        if len(words) > 1:
            unique_words = set(words)
            if len(unique_words) == 1:  # All words are the same
                return True
            
            # Check if more than 70% of words are the same
            most_common_word = max(unique_words, key=words.count)
            if words.count(most_common_word) / len(words) > 0.7:
                return True
        
        # Check for very short meaningless phrases
        if len(words) <= 2 and all(word in ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"] for word in words):
            return True
            
        return False
    
    def _type_text_at_cursor(self, text: str):
        """Type text at cursor position using appropriate tool with multiple fallbacks"""
        if not text.strip():
            return
            
        print(f"🎯 Attempting to type: {text[:50]}...")
        
        # Method 1: Smart window focus + clipboard + paste
        print("🎯 Using smart window focus + clipboard + paste method...")
        try:
            # First, get the window that was focused when we started (not the terminal)
            # We'll look for text editor windows specifically
            result = subprocess.run(['xdotool', 'search', '--onlyvisible', '--class', 'gedit|kate|code|atom|sublime|notepad'], 
                                  capture_output=True, text=True, timeout=5)
            
            target_window = None
            if result.returncode == 0 and result.stdout.strip():
                # Found text editor windows, use the first one
                windows = result.stdout.strip().split('\n')
                target_window = windows[0]
                print(f"🎯 Found text editor window: {target_window}")
                
                # Get window name for confirmation
                try:
                    name_result = subprocess.run(['xdotool', 'getwindowname', target_window], 
                                               capture_output=True, text=True, timeout=5)
                    if name_result.returncode == 0:
                        window_name = name_result.stdout.strip()
                        print(f"🪟 Target window: {window_name}")
                except:
                    pass
            
            # Copy to clipboard first
            if os.environ.get('WAYLAND_DISPLAY'):
                proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=5)
                clipboard_success = proc.returncode == 0
            else:
                proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=5)
                clipboard_success = proc.returncode == 0
            
            if clipboard_success:
                print(f"📋 Text copied to clipboard: {text[:50]}...")
                
                # Small delay to ensure clipboard is ready
                time.sleep(0.2)
                
                if target_window:
                    # Focus the target window first, then paste
                    subprocess.run(['xdotool', 'windowfocus', target_window], check=True, timeout=5)
                    time.sleep(0.1)
                    subprocess.run(['xdotool', 'key', '--window', target_window, 'ctrl+v'], check=True, timeout=5)
                    print(f"✅ Pasted to specific window: {text[:50]}...")
                else:
                    # Fallback to current focused window
                    subprocess.run(['xdotool', 'key', 'ctrl+v'], check=True, timeout=5)
                    print(f"✅ Pasted to focused window: {text[:50]}...")
                
                # Don't show notification to reduce noise - just print success
                return
            else:
                print("⚠️ Failed to copy to clipboard")
                
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Smart paste failed: {e}")
        except subprocess.TimeoutExpired:
            print("⚠️ Smart paste timed out")
        except FileNotFoundError:
            print("⚠️ Required tools not found for smart paste method")
        
        # Method 2: Try wtype for Wayland (if xdotool failed)
        if os.environ.get('WAYLAND_DISPLAY'):
            try:
                subprocess.run(['wtype', text], check=True, timeout=10)
                print(f"✅ Typed via wtype: {text[:50]}...")
                return
            except subprocess.CalledProcessError as e:
                print(f"⚠️ wtype failed: {e}")
            except subprocess.TimeoutExpired:
                print("⚠️ wtype timed out")
            except FileNotFoundError:
                print("⚠️ wtype not found")
        
        # Method 3: Try ydotool (universal input tool)
        try:
            subprocess.run(['ydotool', 'type', text], check=True, timeout=10)
            print(f"✅ Typed via ydotool: {text[:50]}...")
            return
        except subprocess.CalledProcessError as e:
            print(f"⚠️ ydotool failed: {e}")
        except subprocess.TimeoutExpired:
            print("⚠️ ydotool timed out")
        except FileNotFoundError:
            print("⚠️ ydotool not found")
        
        # Method 4: Smart clipboard + paste (most reliable for cursor positioning)
        try:
            print("📋 Trying clipboard + paste method...")
            
            # Copy to clipboard
            if os.environ.get('WAYLAND_DISPLAY'):
                proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=5)
                clipboard_success = proc.returncode == 0
            else:
                proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=5)
                clipboard_success = proc.returncode == 0
            
            if clipboard_success:
                print(f"📋 Text copied to clipboard: {text[:50]}...")
                
                # Now paste it using keyboard shortcut
                time.sleep(0.2)  # Brief delay
                try:
                    # Use xdotool to send Ctrl+V
                    subprocess.run(['xdotool', 'key', 'ctrl+v'], check=True, timeout=5)
                    print(f"✅ Pasted via Ctrl+V: {text[:50]}...")
                    return
                except Exception as paste_error:
                    print(f"⚠️ Paste failed: {paste_error}")
                    print(f"📋 Text copied to clipboard - paste with Ctrl+V: {text[:30]}...")
                    return
            
        except Exception as e:
            print(f"⚠️ Clipboard method failed: {e}")
        
        # Method 5: Show notification with text as last resort
        print(f"❌ All typing methods failed for: {text[:50]}...")
        GLib.idle_add(self.show_notification, "❌ Typing Failed", f"Transcription: {text[:100]}...")
        
        # Also print to console so user can copy manually
        print(f"📝 TRANSCRIBED TEXT: {text}")
        print("💡 You can copy the text above manually")
    
    def start_agent(self, widget):
        """Start the Voxtral agent"""
        if self.agent_process and self.agent_process.poll() is None:
            self.show_notification("⚠️ Agent", "Agent is already running")
            return
        
        try:
            agent_script = project_root / "agent" / "agent_main.py"
            self.agent_process = subprocess.Popen([
                sys.executable, str(agent_script)
            ], cwd=str(project_root))
            
            self.show_notification("✅ Agent", "Agent started successfully")
            
        except Exception as e:
            self.show_notification("❌ Agent", f"Failed to start: {e}")
    
    def stop_agent(self, widget):
        """Stop the Voxtral agent"""
        if not self.agent_process or self.agent_process.poll() is not None:
            self.show_notification("⚠️ Agent", "Agent is not running")
            return
        
        try:
            self.agent_process.terminate()
            try:
                self.agent_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.agent_process.kill()
                self.agent_process.wait()
            
            self.agent_process = None
            self.show_notification("✅ Agent", "Agent stopped")
            
        except Exception as e:
            self.show_notification("❌ Agent", f"Error stopping: {e}")
    
    def restart_agent(self, widget):
        """Restart the Voxtral agent"""
        self.stop_agent(None)
        time.sleep(1)
        self.start_agent(None)
    
    def start_vllm_server(self, widget):
        """Start VLLM server"""
        if self.is_vllm_running():
            self.show_notification("⚠️ VLLM", "Server is already running")
            return
        
        try:
            # Try to start real VLLM server first
            vllm_script = project_root / "scripts" / "start_vllm_cpu.py"
            self.vllm_process = subprocess.Popen([
                sys.executable, str(vllm_script)
            ], cwd=str(project_root))
            
            self.show_notification("🧠 VLLM", "Starting server...")
            
            # Check if it started successfully after a few seconds
            GLib.timeout_add_seconds(10, self._check_vllm_startup)
            
        except Exception as e:
            self.show_notification("❌ VLLM", f"Failed to start: {e}")
    
    def _check_vllm_startup(self):
        """Check if VLLM server started successfully"""
        if self.is_vllm_running():
            self.show_notification("✅ VLLM", "Server started successfully")
        else:
            # Fall back to mock server
            self.show_notification("⚠️ VLLM", "Falling back to mock server...")
            self._start_mock_server()
        return False  # Don't repeat this timeout
    
    def _start_mock_server(self):
        """Start mock VLLM server as fallback"""
        try:
            mock_script = project_root / "scripts" / "mock_vllm_server.py"
            self.mock_server_process = subprocess.Popen([
                sys.executable, str(mock_script)
            ], cwd=str(project_root))
            
            GLib.timeout_add_seconds(3, lambda: self.show_notification("✅ Mock Server", "Mock VLLM server started"))
            
        except Exception as e:
            self.show_notification("❌ Mock Server", f"Failed to start: {e}")
    
    def stop_vllm_server(self, widget):
        """Stop VLLM server"""
        try:
            # Stop our managed processes
            if self.vllm_process:
                self.vllm_process.terminate()
                self.vllm_process = None
            
            if self.mock_server_process:
                self.mock_server_process.terminate()
                self.mock_server_process = None
            
            # Kill any remaining VLLM processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if not proc_info or not proc_info.get('cmdline'):
                        continue
                    
                    cmdline = ' '.join(proc_info['cmdline'])
                    if 'vllm' in cmdline.lower() or 'mock_vllm_server' in cmdline:
                        proc.terminate()
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.show_notification("✅ VLLM", "Server stopped")
            
        except Exception as e:
            self.show_notification("❌ VLLM", f"Error stopping: {e}")
    
    def is_vllm_running(self) -> bool:
        """Check if VLLM server is running"""
        try:
            import requests
            response = requests.get("http://localhost:8000/v1/models", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def open_folder(self, path: str):
        """Open folder in file manager"""
        try:
            subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.show_notification("❌ Error", f"Failed to open folder: {e}")
    
    def open_logs(self, widget):
        """Open log file"""
        log_file = project_root / "voxtral.log"
        if log_file.exists():
            subprocess.Popen(["xdg-open", str(log_file)])
        else:
            self.show_notification("⚠️ Logs", "No log file found")
    
    def open_config(self, widget):
        """Open configuration file"""
        config_file = project_root / "config" / "voxtral.yaml"
        subprocess.Popen(["xdg-open", str(config_file)])
    
    def test_system(self, widget):
        """Run system tests"""
        try:
            test_script = project_root / "scripts" / "test_system.py"
            subprocess.Popen([
                "gnome-terminal", "--", "bash", "-c", 
                f"cd {project_root} && source venv/bin/activate && python {test_script}; read -p 'Press Enter to close...'"
            ])
        except Exception as e:
            self.show_notification("❌ Test", f"Failed to run tests: {e}")
    
    def update_status(self):
        """Update status display"""
        try:
            agent_running = self.agent_process and self.agent_process.poll() is None
            vllm_running = self.is_vllm_running()
            
            if agent_running and vllm_running:
                status = "🟢 Running (Agent + VLLM)"
            elif agent_running:
                status = "🟡 Agent Only"
            elif vllm_running:
                status = "🟡 VLLM Only"
            else:
                status = "🔴 Stopped"
            
            self.status_item.set_label(status)
            
            # Update menu item sensitivity
            self.start_agent_item.set_sensitive(not agent_running)
            self.stop_agent_item.set_sensitive(agent_running)
            self.restart_agent_item.set_sensitive(agent_running)
            
            self.start_vllm_item.set_sensitive(not vllm_running)
            self.stop_vllm_item.set_sensitive(vllm_running)
            
            # Update dictation items based on Whisper availability
            whisper_ready = WHISPER_AVAILABLE and self.whisper_model is not None
            self.quick_record_item.set_sensitive(whisper_ready and not self.is_quick_recording and not self.is_continuous_listening)
            self.continuous_item.set_sensitive(whisper_ready)
            
        except Exception as e:
            print(f"Error updating status: {e}")
        
        return True  # Continue the timer
    
    def update_menu_status(self, status_text):
        """Update menu status text"""
        if hasattr(self, 'status_item'):
            self.status_item.set_label(status_text)
    
    def show_notification(self, title: str, message: str):
        """Show desktop notification"""
        try:
            subprocess.run([
                "notify-send", 
                "--app-name=Voxtral",
                "--icon=audio-input-microphone",
                title, 
                message
            ], check=False)
        except:
            print(f"{title}: {message}")
    
    def quit_application(self, widget):
        """Quit the application"""
        # Stop all processes
        self.stop_agent(None)
        self.stop_vllm_server(None)
        
        Gtk.main_quit()

def main():
    """Main entry point"""
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        Gtk.main_quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check if system tray is available
    if not AppIndicator3.Indicator:
        print("❌ System tray not available. Please install libayatana-appindicator3-1")
        sys.exit(1)
    
    # Create and run tray application
    app = VoxtralTrayGTK()
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()