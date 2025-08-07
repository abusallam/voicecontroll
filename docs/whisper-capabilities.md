# 🎙️ Enhanced Whisper Capabilities Documentation

This document covers all the advanced OpenAI Whisper features integrated into the Voxtral Agentic Voice Platform, providing comprehensive voice transcription capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Installation & Setup](#installation--setup)
- [Model Sizes & Performance](#model-sizes--performance)
- [Core Features](#core-features)
- [Advanced Features](#advanced-features)
- [Real-time Transcription](#real-time-transcription)
- [Word-level Timestamps](#word-level-timestamps)
- [Multilingual Support](#multilingual-support)
- [Configuration Options](#configuration-options)
- [API Reference](#api-reference)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Overview

The Enhanced Whisper Engine provides state-of-the-art speech recognition with the following capabilities:

- **🎯 High Accuracy**: Multiple model sizes from tiny to large-v3
- **🌍 Multilingual**: Support for 99+ languages including Arabic
- **⏱️ Timestamps**: Segment and word-level timing information
- **🔄 Real-time**: Live transcription with configurable chunk sizes
- **🎛️ Flexible**: Extensive configuration options for fine-tuning
- **🚀 Fast**: Optimized for both CPU and GPU processing
- **🔒 Private**: Runs completely locally, no cloud dependencies

## Installation & Setup

### Basic Installation

```bash
# Core Whisper
pip install openai-whisper

# Enhanced features (WhisperX for word timestamps)
pip install git+https://github.com/m-bain/whisperx.git

# Audio processing
pip install soundfile sounddevice

# System dependencies
sudo apt install ffmpeg
```

### GPU Acceleration (Recommended)

```bash
# For NVIDIA GPUs
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU support
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Model Sizes & Performance

| Model | Parameters | VRAM | Speed | Accuracy | Use Case |
|-------|------------|------|-------|----------|----------|
| `tiny` | 39M | ~1GB | ~32x | Good | Real-time, low resources |
| `base` | 74M | ~1GB | ~16x | Better | Balanced performance |
| `small` | 244M | ~2GB | ~6x | Good | Production ready |
| `medium` | 769M | ~5GB | ~2x | Very Good | High accuracy needs |
| `large` | 1550M | ~10GB | ~1x | Excellent | Maximum accuracy |
| `large-v2` | 1550M | ~10GB | ~1x | Excellent | Improved large model |
| `large-v3` | 1550M | ~10GB | ~1x | Best | Latest and most accurate |

**Speed** is relative to real-time (1x = real-time processing)

## Core Features

### Basic Transcription

```python
from models.enhanced_whisper_engine import get_whisper_engine, WhisperConfig, ModelSize

# Create configuration
config = WhisperConfig(
    model_size=ModelSize.BASE,
    language="en",  # or None for auto-detection
    temperature=0.0  # Deterministic output
)

# Get engine instance
engine = get_whisper_engine(config)

# Transcribe file
result = engine.transcribe_file("audio.wav")
print(f"Text: {result.text}")
print(f"Language: {result.language}")
print(f"Confidence: {result.confidence_score:.2f}")
```

### Transcribe Audio Data

```python
import numpy as np

# From numpy array (e.g., from microphone)
audio_data = np.array([...])  # Your audio data
result = engine.transcribe_audio_data(audio_data, sample_rate=16000)
```

## Advanced Features

### Language Detection

```python
# Detect language probabilities
language_probs = engine.detect_language("audio.wav")
for lang, prob in language_probs.items():
    print(f"{lang}: {prob:.3f}")

# Output:
# english (en): 0.987
# spanish (es): 0.008
# french (fr): 0.003
```

### Translation to English

```python
from models.enhanced_whisper_engine import TaskType

config = WhisperConfig(
    model_size=ModelSize.SMALL,
    task=TaskType.TRANSLATE,  # Translate to English
    language="ar"  # Source language (Arabic)
)

engine = get_whisper_engine(config)
result = engine.transcribe_file("arabic_audio.wav")
print(result.text)  # English translation
```

### Segment-level Timestamps

```python
result = engine.transcribe_file("audio.wav")

for segment in result.segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")
    print(f"  Confidence: {segment.avg_logprob:.3f}")
    print(f"  No speech prob: {segment.no_speech_prob:.3f}")
```

## Real-time Transcription

### Live Transcription Setup

```python
def transcription_callback(result):
    """Called for each transcribed chunk"""
    print(f"Live: {result.text}")
    
    # Type the text using enhanced cursor typing
    from tools.enhanced_cursor_typing import cursor_typing_manager
    cursor_typing_manager.type_at_cursor(result.text)

# Start real-time transcription
engine.start_realtime_transcription(
    callback=transcription_callback,
    chunk_duration=3.0  # Process every 3 seconds
)

# Stop when done
engine.stop_realtime_transcription()
```

### Hotkey Integration

```python
from scripts.hotkey_manager import HotkeyManager

def on_hotkey_activation():
    """Start transcription on Ctrl+Alt"""
    engine.start_realtime_transcription(transcription_callback)

def on_hotkey_deactivation():
    """Stop transcription on Ctrl+Alt release"""
    engine.stop_realtime_transcription()

hotkey_manager = HotkeyManager()
hotkey_manager.set_activation_callback(on_hotkey_activation)
hotkey_manager.set_deactivation_callback(on_hotkey_deactivation)
hotkey_manager.register_hotkey()
```

## Word-level Timestamps

### Enable Word Timestamps

```python
config = WhisperConfig(
    model_size=ModelSize.SMALL,
    word_timestamps=True  # Enable word-level timing
)

engine = get_whisper_engine(config)
result = engine.transcribe_file("audio.wav")

# Access word timestamps
for word in result.word_timestamps:
    print(f"'{word.word}' [{word.start:.2f}s - {word.end:.2f}s] (conf: {word.confidence:.3f})")
```

### Real-time Word Highlighting

```python
def highlight_words_callback(result):
    """Highlight words as they're spoken"""
    for word in result.word_timestamps:
        # Schedule word highlighting
        threading.Timer(word.start, lambda w=word: highlight_word(w.word)).start()

def highlight_word(word):
    """Highlight a specific word in UI"""
    print(f"🔆 Highlighting: {word}")
```

## Multilingual Support

### Supported Languages

The engine supports 99+ languages including:

| Language | Code | Language | Code | Language | Code |
|----------|------|----------|------|----------|------|
| English | `en` | Arabic | `ar` | Spanish | `es` |
| French | `fr` | German | `de` | Italian | `it` |
| Portuguese | `pt` | Russian | `ru` | Japanese | `ja` |
| Korean | `ko` | Chinese | `zh` | Hindi | `hi` |
| Turkish | `tr` | Dutch | `nl` | Polish | `pl` |

### Auto-detection vs Forced Language

```python
# Auto-detect language (slower but flexible)
config = WhisperConfig(language=None)

# Force specific language (faster, more accurate)
config = WhisperConfig(language="ar")  # Arabic

# Get supported languages
engine = get_whisper_engine()
languages = engine.supported_languages
print(f"Supported: {len(languages)} languages")
```

## Configuration Options

### Complete Configuration

```python
from models.enhanced_whisper_engine import WhisperConfig, ModelSize, TaskType

config = WhisperConfig(
    # Model settings
    model_size=ModelSize.SMALL,
    
    # Language settings
    language="en",  # None for auto-detection
    task=TaskType.TRANSCRIBE,  # or TRANSLATE
    
    # Quality settings
    temperature=0.0,  # 0.0 = deterministic, higher = more creative
    best_of=1,  # Number of candidates to consider
    beam_size=5,  # Beam search width
    
    # Filtering settings
    compression_ratio_threshold=2.4,  # Filter repetitive text
    logprob_threshold=-1.0,  # Filter low-confidence segments
    no_speech_threshold=0.6,  # Filter silence
    
    # Advanced settings
    word_timestamps=True,  # Enable word-level timing
    condition_on_previous_text=True,  # Use context
    initial_prompt="",  # Bias the model
    
    # Performance settings
    fp16=True,  # Use half precision (faster on GPU)
    verbose=False  # Debug output
)
```

### Configuration from YAML

Add to `config/voxtral.yaml`:

```yaml
whisper:
  model_size: "small"
  language: null  # Auto-detect
  task: "transcribe"
  temperature: 0.0
  word_timestamps: true
  verbose: false
  
  # Performance settings
  fp16: true
  best_of: 1
  beam_size: 5
  
  # Quality filters
  compression_ratio_threshold: 2.4
  logprob_threshold: -1.0
  no_speech_threshold: 0.6
```

Load configuration:

```python
from models.enhanced_whisper_engine import create_whisper_config_from_settings

config = create_whisper_config_from_settings()
engine = get_whisper_engine(config)
```

## API Reference

### EnhancedWhisperEngine Class

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `load_model(force_reload=False)` | Load Whisper model | `bool` |
| `transcribe_file(audio_path)` | Transcribe audio file | `TranscriptionResult` |
| `transcribe_audio_data(data, sr)` | Transcribe numpy array | `TranscriptionResult` |
| `detect_language(audio_path)` | Detect language probabilities | `Dict[str, float]` |
| `start_realtime_transcription(callback, chunk_duration)` | Start live transcription | `bool` |
| `stop_realtime_transcription()` | Stop live transcription | `None` |
| `get_model_info()` | Get model information | `Dict[str, Any]` |
| `benchmark_model(test_audio)` | Benchmark performance | `Dict[str, float]` |
| `update_config(**kwargs)` | Update configuration | `bool` |

#### TranscriptionResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `text` | `str` | Complete transcribed text |
| `language` | `str` | Detected/specified language |
| `segments` | `List[TranscriptionSegment]` | Timed segments |
| `word_timestamps` | `List[WordTimestamp]` | Word-level timing |
| `processing_time` | `float` | Time taken to process |
| `model_used` | `str` | Model size used |
| `confidence_score` | `float` | Overall confidence (0-1) |

## Performance Optimization

### GPU Optimization

```python
# Check GPU availability
engine = get_whisper_engine()
info = engine.get_model_info()
print(f"Device: {info['device']}")

# Benchmark performance
benchmark = engine.benchmark_model()
print(f"Real-time factor: {benchmark['real_time_factor']:.2f}x")
print(f"Characters/second: {benchmark['characters_per_second']:.1f}")
```

### Memory Optimization

```python
# Use smaller model for real-time
config = WhisperConfig(
    model_size=ModelSize.TINY,  # Lowest memory usage
    fp16=True,  # Half precision
    word_timestamps=False  # Disable if not needed
)

# Batch processing for multiple files
files = ["audio1.wav", "audio2.wav", "audio3.wav"]
results = []

engine = get_whisper_engine(config)
for file in files:
    result = engine.transcribe_file(file)
    results.append(result)
    # Model stays loaded between files
```

### Speed Optimization

```python
# Fastest configuration
fast_config = WhisperConfig(
    model_size=ModelSize.TINY,
    language="en",  # Don't auto-detect
    temperature=0.0,  # Deterministic
    best_of=1,  # Single candidate
    beam_size=1,  # Greedy search
    word_timestamps=False,  # Disable if not needed
    condition_on_previous_text=False  # Disable context
)
```

## Troubleshooting

### Common Issues

#### 1. CUDA Out of Memory

```python
# Solution: Use smaller model or CPU
config = WhisperConfig(
    model_size=ModelSize.SMALL,  # Instead of LARGE
    fp16=False  # Disable if GPU doesn't support
)

# Or force CPU usage
import torch
torch.cuda.set_device(-1)  # Force CPU
```

#### 2. Poor Transcription Quality

```python
# Solution: Use larger model and optimize settings
config = WhisperConfig(
    model_size=ModelSize.MEDIUM,  # Larger model
    language="en",  # Specify language
    temperature=0.0,  # Deterministic
    compression_ratio_threshold=2.4,  # Filter repetition
    no_speech_threshold=0.6  # Filter silence
)
```

#### 3. Slow Real-time Performance

```python
# Solution: Optimize for speed
config = WhisperConfig(
    model_size=ModelSize.TINY,  # Fastest model
    language="en",  # Don't auto-detect
    word_timestamps=False,  # Disable if not needed
    beam_size=1  # Greedy decoding
)

# Use shorter chunks
engine.start_realtime_transcription(callback, chunk_duration=2.0)
```

#### 4. Word Timestamps Not Working

```bash
# Install WhisperX
pip install git+https://github.com/m-bain/whisperx.git

# Check availability
python -c "import whisperx; print('WhisperX available')"
```

### Debug Mode

```python
# Enable verbose output
config = WhisperConfig(verbose=True)
engine = get_whisper_engine(config)

# Check model info
info = engine.get_model_info()
print(f"Model info: {info}")

# Benchmark performance
benchmark = engine.benchmark_model()
print(f"Benchmark: {benchmark}")
```

### Performance Monitoring

```python
import time

def monitor_transcription(audio_file):
    start_time = time.time()
    
    result = engine.transcribe_file(audio_file)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"File: {audio_file}")
    print(f"Duration: {result.processing_time:.2f}s")
    print(f"Text length: {len(result.text)} chars")
    print(f"Segments: {len(result.segments)}")
    print(f"Confidence: {result.confidence_score:.3f}")
    print(f"Real-time factor: {processing_time / result.processing_time:.2f}x")
```

## Integration Examples

### With Hotkey System

```python
from scripts.hotkey_manager import HotkeyManager
from models.enhanced_whisper_engine import get_whisper_engine, WhisperConfig, ModelSize

# Setup
config = WhisperConfig(model_size=ModelSize.BASE, language="en")
engine = get_whisper_engine(config)
hotkey_manager = HotkeyManager()

def start_voice_transcription():
    def transcription_callback(result):
        # Type the transcribed text
        from tools.enhanced_cursor_typing import cursor_typing_manager
        cursor_typing_manager.type_at_cursor(result.text)
    
    engine.start_realtime_transcription(transcription_callback, chunk_duration=3.0)

def stop_voice_transcription():
    engine.stop_realtime_transcription()

# Register hotkeys
hotkey_manager.set_activation_callback(start_voice_transcription)
hotkey_manager.set_deactivation_callback(stop_voice_transcription)
hotkey_manager.register_hotkey()
```

### With Tray Application

```python
# In scripts/voxtral_tray_unified.py
def _hotkey_voice_activation(self):
    """Handle hotkey voice activation"""
    if not self.whisper_engine:
        config = create_whisper_config_from_settings()
        self.whisper_engine = get_whisper_engine(config)
    
    def transcription_callback(result):
        # Process transcription result
        self._type_text_enhanced(result.text)
        
        # Show notification
        GLib.idle_add(self.show_notification, "Voice Transcribed", 
                     f"Typed: {result.text[:50]}...")
    
    self.whisper_engine.start_realtime_transcription(transcription_callback)
```

## Future Enhancements

### Planned Features

- **🎯 Custom Model Training**: Fine-tune models for specific domains
- **🔊 Noise Reduction**: Preprocessing for better quality
- **📊 Analytics**: Detailed transcription analytics
- **🌐 Streaming**: WebSocket-based real-time streaming
- **🎨 UI Integration**: Visual waveform and transcript display
- **📱 Mobile Support**: Cross-platform compatibility

### Contributing

To contribute to the Whisper capabilities:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/whisper-enhancement`
3. **Add tests**: Ensure new features are tested
4. **Update documentation**: Keep this document current
5. **Submit PR**: Include detailed description of changes

---

**Built with ❤️ for the Linux community! 🐧🎙️**

*Last updated: August 2025*