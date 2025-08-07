#!/usr/bin/env python3
"""
Direct voice test with enhanced typing - no tray needed
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add user packages path
user_packages = os.path.expanduser('~/.local/lib/python3.11/site-packages')
if user_packages not in sys.path:
    sys.path.insert(0, user_packages)

try:
    import sounddevice as sd
    import numpy as np
    import whisper
    import soundfile as sf
    print("✅ All libraries available")
except ImportError as e:
    print(f"❌ Missing libraries: {e}")
    sys.exit(1)

def test_voice_with_direct_typing():
    """Test voice transcription with direct typing"""
    print("🎙️ Direct Voice Test with Enhanced Typing")
    print("=" * 50)
    
    # Load Whisper model
    print("🧠 Loading Whisper model...")
    model = whisper.load_model("base")
    print("✅ Model loaded")
    
    # Record audio
    duration = 5
    sample_rate = 16000
    
    print(f"\n🔴 Recording for {duration} seconds...")
    print("💬 Speak now: Say something you want to type")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"   Starting in {i}...")
        time.sleep(1)
    
    print("🎤 RECORDING NOW - SPEAK!")
    
    # Record
    audio_data = sd.rec(int(duration * sample_rate), 
                       samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    
    print("⏹️ Recording finished")
    
    # Check audio level
    rms_energy = np.sqrt(np.mean(audio_data ** 2))
    print(f"🔊 Audio level: {rms_energy:.6f}")
    
    if rms_energy < 0.01:
        print("⚠️ Audio level very low - make sure microphone is working")
        return
    
    # Save to temporary file
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        sf.write(temp_file.name, audio_data, sample_rate)
        temp_path = temp_file.name
    
    try:
        # Transcribe
        print("🧠 Transcribing...")
        result = model.transcribe(temp_path, language="en")
        
        transcript = result["text"].strip()
        
        print(f"\n📝 TRANSCRIPTION RESULT:")
        print(f"   Text: '{transcript}'")
        
        if transcript:
            print(f"\n✅ SUCCESS! Transcribed: {len(transcript)} characters")
            
            # Try direct typing with sudo ydotool
            print(f"⌨️ Attempting direct typing with sudo ydotool...")
            print(f"💡 Please focus a text editor and wait 3 seconds...")
            
            time.sleep(3)
            
            try:
                import subprocess
                
                # Use sudo ydotool directly
                cmd = ['sudo', 'ydotool', 'type', transcript]
                print(f"🔧 Running: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    print(f"✅ SUCCESS! Text typed directly using sudo ydotool")
                    print(f"🎯 The text should appear where your cursor was positioned")
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    print(f"❌ ydotool failed: {error_msg}")
                    
                    # Fallback to clipboard
                    print(f"📋 Falling back to clipboard...")
                    if os.environ.get('WAYLAND_DISPLAY'):
                        proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
                        proc.communicate(input=transcript, timeout=5)
                        print(f"📋 Text copied to clipboard - press Ctrl+V to paste")
                    
            except Exception as e:
                print(f"❌ Typing error: {e}")
                print(f"📋 Manual copy: {transcript}")
        else:
            print("⚠️ No speech detected or transcription failed")
            
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    try:
        test_voice_with_direct_typing()
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()