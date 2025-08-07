#!/usr/bin/env python3
"""
Enhanced Whisper Engine for Voxtral Agent
Implements all advanced Whisper features for maximum transcription capabilities
Supports word-level timestamps, real-time processing, multilingual, and more
"""

import os
import sys
import time
import tempfile
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import Whisper and related libraries
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    print("⚠️ OpenAI Whisper not available. Install with: pip install openai-whisper")
    WHISPER_AVAILABLE = False

try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    print("⚠️ WhisperX not available. Install with: pip install git+https://github.com/m-bain/whisperx.git")
    WHISPERX_AVAILABLE = False

try:
    import soundfile as sf
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    print("⚠️ Audio libraries not available. Install with: pip install soundfile sounddevice")
    AUDIO_AVAILABLE = False

from config.settings import config

class ModelSize(Enum):
    """Whisper model sizes"""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"

class TaskType(Enum):
    """Whisper task types"""
    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"

@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing"""
    id: int
    start: float
    end: float
    text: str
    tokens: List[int] = field(default_factory=list)
    temperature: float = 0.0
    avg_logprob: float = 0.0
    compression_ratio: float = 0.0
    no_speech_prob: float = 0.0

@dataclass
class WordTimestamp:
    """Word-level timestamp information"""
    word: str
    start: float
    end: float
    confidence: float = 0.0

@dataclass
class TranscriptionResult:
    """Complete transcription result with all metadata"""
    text: str
    language: str
    segments: List[TranscriptionSegment] = field(default_factory=list)
    word_timestamps: List[WordTimestamp] = field(default_factory=list)
    processing_time: float = 0.0
    model_used: str = ""
    confidence_score: float = 0.0

@dataclass
class WhisperConfig:
    """Configuration for Whisper engine"""
    model_size: ModelSize = ModelSize.BASE
    language: Optional[str] = None  # Auto-detect if None
    task: TaskType = TaskType.TRANSCRIBE
    temperature: float = 0.0
    best_of: int = 1
    beam_size: int = 5
    patience: float = 1.0
    length_penalty: float = 1.0
    suppress_tokens: str = "-1"
    initial_prompt: Optional[str] = None
    condition_on_previous_text: bool = True
    fp16: bool = True
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    word_timestamps: bool = False
    prepend_punctuations: str = "\"'([{-"
    append_punctuations: str = "\"'.,:!?)]}"
    verbose: bool = False

class EnhancedWhisperEngine:
    """Enhanced Whisper engine with all advanced features"""
    
    def __init__(self, config: Optional[WhisperConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or WhisperConfig()
        
        # Models
        self.whisper_model = None
        self.whisperx_model = None
        self.alignment_model = None
        self.alignment_metadata = None
        
        # State
        self.is_loaded = False
        self.device = self._detect_device()
        self.supported_languages = self._get_supported_languages()
        
        # Real-time processing
        self.is_realtime_active = False
        self.realtime_callback = None
        self.audio_buffer = []
        self.sample_rate = 16000
        
        self.logger.info(f"Enhanced Whisper Engine initialized with device: {self.device}")
    
    def _detect_device(self) -> str:
        """Detect the best available device"""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"
    
    def _get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages"""
        if not WHISPER_AVAILABLE:
            return {}
        
        try:
            return whisper.tokenizer.LANGUAGES
        except:
            # Fallback list of common languages
            return {
                "en": "english",
                "ar": "arabic",
                "es": "spanish",
                "fr": "french",
                "de": "german",
                "it": "italian",
                "pt": "portuguese",
                "ru": "russian",
                "ja": "japanese",
                "ko": "korean",
                "zh": "chinese"
            }
    
    def load_model(self, force_reload: bool = False) -> bool:
        """Load the Whisper model with current configuration"""
        if self.is_loaded and not force_reload:
            return True
        
        if not WHISPER_AVAILABLE:
            self.logger.error("Whisper not available")
            return False
        
        try:
            self.logger.info(f"Loading Whisper model: {self.config.model_size.value}")
            start_time = time.time()
            
            # Load main Whisper model
            self.whisper_model = whisper.load_model(
                self.config.model_size.value,
                device=self.device
            )
            
            # Load WhisperX model if available and word timestamps requested
            if WHISPERX_AVAILABLE and self.config.word_timestamps:
                self.logger.info("Loading WhisperX for word-level timestamps")
                self.whisperx_model = whisperx.load_model(
                    self.config.model_size.value,
                    device=self.device
                )
            
            load_time = time.time() - start_time
            self.is_loaded = True
            
            self.logger.info(f"✅ Model loaded successfully in {load_time:.2f}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False
    
    def transcribe_file(self, audio_path: str) -> TranscriptionResult:
        """Transcribe an audio file with full feature support"""
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError("Failed to load Whisper model")
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Transcribing file: {audio_path}")
            
            # Prepare transcription options
            options = {
                "language": self.config.language,
                "task": self.config.task.value,
                "temperature": self.config.temperature,
                "best_of": self.config.best_of,
                "beam_size": self.config.beam_size,
                "patience": self.config.patience,
                "length_penalty": self.config.length_penalty,
                "suppress_tokens": self.config.suppress_tokens,
                "initial_prompt": self.config.initial_prompt,
                "condition_on_previous_text": self.config.condition_on_previous_text,
                "fp16": self.config.fp16,
                "compression_ratio_threshold": self.config.compression_ratio_threshold,
                "logprob_threshold": self.config.logprob_threshold,
                "no_speech_threshold": self.config.no_speech_threshold,
                "verbose": self.config.verbose,
                "prepend_punctuations": self.config.prepend_punctuations,
                "append_punctuations": self.config.append_punctuations
            }
            
            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(audio_path, **options)
            
            # Convert segments
            segments = []
            for seg in result.get("segments", []):
                segments.append(TranscriptionSegment(
                    id=seg.get("id", 0),
                    start=seg.get("start", 0.0),
                    end=seg.get("end", 0.0),
                    text=seg.get("text", ""),
                    tokens=seg.get("tokens", []),
                    temperature=seg.get("temperature", 0.0),
                    avg_logprob=seg.get("avg_logprob", 0.0),
                    compression_ratio=seg.get("compression_ratio", 0.0),
                    no_speech_prob=seg.get("no_speech_prob", 0.0)
                ))
            
            # Get word-level timestamps if requested
            word_timestamps = []
            if self.config.word_timestamps and WHISPERX_AVAILABLE and self.whisperx_model:
                word_timestamps = self._get_word_timestamps(audio_path, result)
            
            processing_time = time.time() - start_time
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(segments)
            
            transcription_result = TranscriptionResult(
                text=result["text"],
                language=result.get("language", "unknown"),
                segments=segments,
                word_timestamps=word_timestamps,
                processing_time=processing_time,
                model_used=self.config.model_size.value,
                confidence_score=confidence_score
            )
            
            self.logger.info(f"✅ Transcription completed in {processing_time:.2f}s")
            return transcription_result
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise
    
    def transcribe_audio_data(self, audio_data: np.ndarray, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe audio data directly from numpy array"""
        # Save to temporary file and transcribe
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)
            temp_path = temp_file.name
        
        try:
            result = self.transcribe_file(temp_path)
            return result
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _get_word_timestamps(self, audio_path: str, whisper_result: Dict) -> List[WordTimestamp]:
        """Get word-level timestamps using WhisperX"""
        if not WHISPERX_AVAILABLE or not self.whisperx_model:
            return []
        
        try:
            self.logger.info("Generating word-level timestamps...")
            
            # Load audio for WhisperX
            audio = whisperx.load_audio(audio_path)
            
            # Load alignment model if not already loaded
            if not self.alignment_model:
                language_code = whisper_result.get("language", "en")
                self.alignment_model, self.alignment_metadata = whisperx.load_align_model(
                    language_code=language_code,
                    device=self.device
                )
            
            # Align the segments
            result_aligned = whisperx.align(
                whisper_result["segments"],
                self.alignment_model,
                self.alignment_metadata,
                audio,
                device=self.device,
                return_char_alignments=False
            )
            
            # Extract word timestamps
            word_timestamps = []
            for segment in result_aligned.get("segments", []):
                for word_info in segment.get("words", []):
                    word_timestamps.append(WordTimestamp(
                        word=word_info.get("word", ""),
                        start=word_info.get("start", 0.0),
                        end=word_info.get("end", 0.0),
                        confidence=word_info.get("score", 0.0)
                    ))
            
            self.logger.info(f"✅ Generated {len(word_timestamps)} word timestamps")
            return word_timestamps
            
        except Exception as e:
            self.logger.error(f"Word timestamp generation failed: {e}")
            return []
    
    def _calculate_confidence(self, segments: List[TranscriptionSegment]) -> float:
        """Calculate overall confidence score from segments"""
        if not segments:
            return 0.0
        
        # Use average log probability as confidence indicator
        total_logprob = sum(seg.avg_logprob for seg in segments)
        avg_logprob = total_logprob / len(segments)
        
        # Convert log probability to confidence (0-1 scale)
        # This is a heuristic - adjust based on your needs
        confidence = max(0.0, min(1.0, (avg_logprob + 1.0) / 1.0))
        return confidence
    
    def start_realtime_transcription(self, callback: Callable[[TranscriptionResult], None],
                                   chunk_duration: float = 3.0) -> bool:
        """Start real-time transcription with callback"""
        if not AUDIO_AVAILABLE:
            self.logger.error("Audio libraries not available for real-time transcription")
            return False
        
        if self.is_realtime_active:
            self.logger.warning("Real-time transcription already active")
            return False
        
        if not self.is_loaded:
            if not self.load_model():
                return False
        
        self.is_realtime_active = True
        self.realtime_callback = callback
        
        # Start real-time processing thread
        threading.Thread(
            target=self._realtime_processing_loop,
            args=(chunk_duration,),
            daemon=True
        ).start()
        
        self.logger.info(f"✅ Real-time transcription started (chunk: {chunk_duration}s)")
        return True
    
    def stop_realtime_transcription(self):
        """Stop real-time transcription"""
        self.is_realtime_active = False
        self.realtime_callback = None
        self.audio_buffer.clear()
        self.logger.info("Real-time transcription stopped")
    
    def _realtime_processing_loop(self, chunk_duration: float):
        """Real-time processing loop"""
        chunk_samples = int(self.sample_rate * chunk_duration)
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=1024
            ) as stream:
                
                while self.is_realtime_active:
                    # Read audio chunk
                    audio_chunk, _ = stream.read(chunk_samples)
                    audio_data = audio_chunk.flatten()
                    
                    # Check if there's enough audio energy
                    rms_energy = np.sqrt(np.mean(audio_data ** 2))
                    if rms_energy < 0.01:  # Silence threshold
                        continue
                    
                    # Transcribe chunk
                    try:
                        result = self.transcribe_audio_data(audio_data, self.sample_rate)
                        
                        # Call callback if text is meaningful
                        if result.text.strip() and self.realtime_callback:
                            self.realtime_callback(result)
                            
                    except Exception as e:
                        self.logger.error(f"Real-time chunk processing error: {e}")
                        continue
                    
        except Exception as e:
            self.logger.error(f"Real-time processing loop error: {e}")
        finally:
            self.is_realtime_active = False
    
    def detect_language(self, audio_path: str) -> Dict[str, float]:
        """Detect language probabilities for audio file"""
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError("Failed to load Whisper model")
        
        try:
            # Load audio
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.whisper_model.device)
            
            # Detect language
            _, probs = self.whisper_model.detect_language(mel)
            
            # Convert to readable format
            language_probs = {}
            for lang_code, prob in probs.items():
                lang_name = self.supported_languages.get(lang_code, lang_code)
                language_probs[f"{lang_name} ({lang_code})"] = float(prob)
            
            # Sort by probability
            language_probs = dict(sorted(language_probs.items(), key=lambda x: x[1], reverse=True))
            
            return language_probs
            
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return {}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_size": self.config.model_size.value,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "whisper_available": WHISPER_AVAILABLE,
            "whisperx_available": WHISPERX_AVAILABLE,
            "word_timestamps_enabled": self.config.word_timestamps,
            "supported_languages": len(self.supported_languages),
            "realtime_active": self.is_realtime_active
        }
    
    def update_config(self, **kwargs) -> bool:
        """Update configuration and reload model if necessary"""
        reload_needed = False
        
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                setattr(self.config, key, value)
                
                # Check if model reload is needed
                if key in ["model_size", "word_timestamps"] and old_value != value:
                    reload_needed = True
        
        if reload_needed and self.is_loaded:
            self.logger.info("Configuration changed, reloading model...")
            return self.load_model(force_reload=True)
        
        return True
    
    def benchmark_model(self, test_audio_path: Optional[str] = None) -> Dict[str, float]:
        """Benchmark the model performance"""
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError("Failed to load Whisper model")
        
        # Create test audio if not provided
        if not test_audio_path:
            # Generate 10 seconds of test audio
            duration = 10
            sample_rate = 16000
            t = np.linspace(0, duration, duration * sample_rate)
            test_audio = 0.1 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, test_audio, sample_rate)
                test_audio_path = temp_file.name
            
            cleanup_test_file = True
        else:
            cleanup_test_file = False
        
        try:
            # Benchmark transcription
            start_time = time.time()
            result = self.transcribe_file(test_audio_path)
            transcription_time = time.time() - start_time
            
            # Get audio duration
            audio_info = sf.info(test_audio_path)
            audio_duration = audio_info.duration
            
            # Calculate metrics
            real_time_factor = transcription_time / audio_duration
            
            benchmark_results = {
                "transcription_time": transcription_time,
                "audio_duration": audio_duration,
                "real_time_factor": real_time_factor,
                "characters_per_second": len(result.text) / transcription_time if transcription_time > 0 else 0,
                "confidence_score": result.confidence_score,
                "segments_count": len(result.segments),
                "word_timestamps_count": len(result.word_timestamps)
            }
            
            return benchmark_results
            
        finally:
            if cleanup_test_file and os.path.exists(test_audio_path):
                os.unlink(test_audio_path)

# Global instance
enhanced_whisper_engine = None

def get_whisper_engine(config: Optional[WhisperConfig] = None) -> EnhancedWhisperEngine:
    """Get or create the global Whisper engine instance"""
    global enhanced_whisper_engine
    
    if enhanced_whisper_engine is None:
        enhanced_whisper_engine = EnhancedWhisperEngine(config)
    
    return enhanced_whisper_engine

def create_whisper_config_from_settings() -> WhisperConfig:
    """Create WhisperConfig from application settings"""
    whisper_settings = config.get("whisper", {})
    
    return WhisperConfig(
        model_size=ModelSize(whisper_settings.get("model_size", "base")),
        language=whisper_settings.get("language"),
        task=TaskType(whisper_settings.get("task", "transcribe")),
        temperature=whisper_settings.get("temperature", 0.0),
        word_timestamps=whisper_settings.get("word_timestamps", False),
        verbose=whisper_settings.get("verbose", False)
    )