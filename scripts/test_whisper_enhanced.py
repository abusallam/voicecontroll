#!/usr/bin/env python3
"""
Test script for enhanced Whisper functionality
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
    from models.enhanced_whisper_engine import get_whisper_engine, WhisperConfig, ModelSize
    print("✅ Enhanced Whisper engine imported successfully")
except ImportError as e:
    print(f"❌ Failed to import enhanced Whisper engine: {e}")
    sys.exit(1)

def test_whisper_basic():
    """Test basic Whisper functionality"""
    print("\n🧪 Testing Enhanced Whisper Engine")
    print("=" * 50)
    
    # Create configuration
    config = WhisperConfig(
        model_size=ModelSize.BASE,
        language="en",
        temperature=0.0,
        verbose=True
    )
    
    print(f"📋 Configuration:")
    print(f"  Model: {config.model_size.value}")
    print(f"  Language: {config.language}")
    print(f"  Temperature: {config.temperature}")
    
    # Get engine
    print("\n🔧 Initializing Whisper engine...")
    engine = get_whisper_engine(config)
    
    # Get model info
    info = engine.get_model_info()
    print(f"\n📊 Model Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Load model
    print(f"\n🧠 Loading model...")
    start_time = time.time()
    
    if engine.load_model():
        load_time = time.time() - start_time
        print(f"✅ Model loaded successfully in {load_time:.2f}s")
        
        # Test with a simple audio file (if available)
        test_audio_files = [
            "/usr/share/sounds/alsa/Front_Left.wav",
            "/usr/share/sounds/sound-icons/bell.wav",
            "/usr/share/sounds/generic.wav"
        ]
        
        test_file = None
        for audio_file in test_audio_files:
            if os.path.exists(audio_file):
                test_file = audio_file
                break
        
        if test_file:
            print(f"\n🎵 Testing with audio file: {test_file}")
            try:
                result = engine.transcribe_file(test_file)
                print(f"📝 Transcription result:")
                print(f"  Text: '{result.text}'")
                print(f"  Language: {result.language}")
                print(f"  Processing time: {result.processing_time:.2f}s")
                print(f"  Confidence: {result.confidence_score:.3f}")
                print(f"  Segments: {len(result.segments)}")
            except Exception as e:
                print(f"⚠️ Transcription test failed: {e}")
        else:
            print("⚠️ No test audio files found, skipping transcription test")
        
        # Benchmark
        print(f"\n⚡ Running benchmark...")
        try:
            benchmark = engine.benchmark_model()
            print(f"📊 Benchmark Results:")
            for key, value in benchmark.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"⚠️ Benchmark failed: {e}")
        
    else:
        print("❌ Failed to load model")
        return False
    
    return True

def test_real_time_capability():
    """Test real-time transcription capability"""
    print("\n🎙️ Testing Real-time Capability")
    print("=" * 50)
    
    try:
        import sounddevice as sd
        import numpy as np
        print("✅ Audio libraries available")
        
        # Test microphone access
        print("🎤 Testing microphone access...")
        try:
            # Record 1 second of audio to test microphone
            duration = 1
            sample_rate = 16000
            
            print("   Recording 1 second of audio...")
            audio_data = sd.rec(int(duration * sample_rate), 
                              samplerate=sample_rate, channels=1, dtype=np.float32)
            sd.wait()
            
            # Check if we got audio data
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            print(f"   Audio captured - RMS energy: {rms_energy:.6f}")
            
            if rms_energy > 0.001:
                print("✅ Microphone is working and capturing audio")
            else:
                print("⚠️ Microphone captured very quiet audio - check microphone settings")
            
            return True
            
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Audio libraries not available: {e}")
        return False

def main():
    """Main test function"""
    print("🎙️ Enhanced Whisper Test Suite")
    print("=" * 60)
    
    # Test basic functionality
    basic_success = test_whisper_basic()
    
    # Test real-time capability
    realtime_success = test_real_time_capability()
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 30)
    print(f"Basic Whisper: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"Real-time Audio: {'✅ PASS' if realtime_success else '❌ FAIL'}")
    
    if basic_success and realtime_success:
        print(f"\n🎉 All tests passed! Voice transcription should work.")
        print(f"💡 Try using the tray menu or Ctrl+Alt hotkey for voice input.")
    else:
        print(f"\n⚠️ Some tests failed. Check the error messages above.")
    
    return basic_success and realtime_success

if __name__ == "__main__":
    main()