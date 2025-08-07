#!/usr/bin/env python3
"""
Simple voice transcription test - record and transcribe immediately
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
    print("✅ All audio libraries available")
except ImportError as e:
    print(f"❌ Missing libraries: {e}")
    sys.exit(1)

def record_and_transcribe():
    """Record 5 seconds of audio and transcribe it"""
    print("🎙️ Voice Transcription Test")
    print("=" * 40)
    
    # Load Whisper model
    print("🧠 Loading Whisper model...")
    model = whisper.load_model("base")
    print("✅ Model loaded")
    
    # Record audio
    duration = 5
    sample_rate = 16000
    
    print(f"\n🔴 Recording for {duration} seconds...")
    print("💬 Speak now: Say something like 'Hello, this is a test'")
    
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
    import soundfile as sf
    
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
        print(f"   Language: {result.get('language', 'unknown')}")
        
        if transcript:
            print(f"\n✅ SUCCESS! Transcribed: {len(transcript)} characters")
            
            # Try to type it using enhanced cursor typing
            try:
                from tools.enhanced_cursor_typing import cursor_typing_manager
                print(f"⌨️ Attempting to type the text...")
                
                typing_result = cursor_typing_manager.type_at_cursor(transcript)
                
                if typing_result.success:
                    if typing_result.fallback_used:
                        print(f"📋 Text copied to clipboard - press Ctrl+V to paste")
                    else:
                        print(f"✅ Text typed successfully using {typing_result.method_used}")
                else:
                    print(f"⚠️ Typing failed: {typing_result.error_message}")
                    print(f"📋 Text copied to clipboard - press Ctrl+V to paste")
                    
            except Exception as e:
                print(f"⚠️ Enhanced typing error: {e}")
                print(f"📋 Manual copy: {transcript}")
        else:
            print("⚠️ No speech detected or transcription failed")
            
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    try:
        record_and_transcribe()
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()