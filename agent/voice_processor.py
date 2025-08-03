#!/usr/bin/env python3
"""
Voice Processing Module for Voxtral Agent
Handles audio capture, silence detection, and transcription
"""

import asyncio
import logging
import numpy as np
import sounddevice as sd
import threading
import time
from typing import Optional, Callable, Any
from collections import deque
import webrtcvad
from config.settings import config

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Handles real-time voice processing with silence detection and hush word support"""
    
    def __init__(self, transcription_callback: Optional[Callable] = None):
        self.transcription_callback = transcription_callback
        self.is_recording = False
        self.is_listening = False
        
        # Audio configuration
        self.sample_rate = config.get("voice", {}).get("sample_rate", 16000)
        self.chunk_size = config.get("voice", {}).get("chunk_size", 1024)
        self.channels = config.get("voice", {}).get("channels", 1)
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3
        self.silence_threshold = config.get("voice", {}).get("silence_threshold", 0.01)
        self.silence_duration = config.get("voice", {}).get("silence_duration", 2.0)
        self.hush_word = config.get("voice", {}).get("hush_word", "__stop__")
        
        # Audio buffers
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 30))  # 30 seconds max
        self.recording_buffer = []
        
        # State tracking
        self.last_voice_time = 0
        self.recording_start_time = 0
        self.push_to_talk = config.get("voice", {}).get("push_to_talk", False)
        self.continuous_mode = config.get("voice", {}).get("continuous_mode", True)
        
        # Threading
        self.audio_thread = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        
    def start_listening(self):
        """Start the voice processing system"""
        if self.is_listening:
            logger.warning("Voice processor already listening")
            return
        
        self.is_listening = True
        self.stop_event.clear()
        
        # Start audio capture thread
        self.audio_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self.audio_thread.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        logger.info("Voice processor started")
    
    def stop_listening(self):
        """Stop the voice processing system"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        self.stop_event.set()
        
        # Wait for threads to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2)
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2)
        
        logger.info("Voice processor stopped")
    
    def _audio_capture_loop(self):
        """Main audio capture loop"""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=self._audio_callback
            ) as stream:
                logger.info(f"Audio stream started: {self.sample_rate}Hz, {self.channels} channel(s)")
                
                while not self.stop_event.wait(0.1):
                    pass  # Keep stream alive
                    
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
    
    def _audio_callback(self, indata, frames, time, status):
        """Audio input callback"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Convert to mono if needed
        if indata.shape[1] > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata[:, 0]
        
        # Add to buffer
        self.audio_buffer.extend(audio_data)
    
    def _processing_loop(self):
        """Main processing loop for voice activity detection"""
        frame_duration = 30  # ms
        frame_size = int(self.sample_rate * frame_duration / 1000)
        
        while not self.stop_event.is_set():
            try:
                # Check if we have enough audio data
                if len(self.audio_buffer) < frame_size:
                    time.sleep(0.01)
                    continue
                
                # Extract frame
                frame = np.array([self.audio_buffer.popleft() for _ in range(frame_size)])
                
                # Voice activity detection
                is_speech = self._detect_voice_activity(frame)
                current_time = time.time()
                
                if is_speech:
                    self.last_voice_time = current_time
                    
                    if not self.is_recording:
                        self._start_recording()
                    
                    # Add frame to recording buffer
                    self.recording_buffer.extend(frame)
                
                elif self.is_recording:
                    # Check for silence timeout
                    silence_duration = current_time - self.last_voice_time
                    
                    if silence_duration >= self.silence_duration:
                        self._stop_recording()
                    else:
                        # Continue recording during short silences
                        self.recording_buffer.extend(frame)
                
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                time.sleep(0.1)
    
    def _detect_voice_activity(self, frame: np.ndarray) -> bool:
        """Detect voice activity in audio frame"""
        try:
            # Convert to 16-bit PCM for WebRTC VAD
            pcm_frame = (frame * 32767).astype(np.int16).tobytes()
            
            # WebRTC VAD requires specific frame sizes
            if len(pcm_frame) != frame.shape[0] * 2:
                return False
            
            # Use WebRTC VAD
            is_speech = self.vad.is_speech(pcm_frame, self.sample_rate)
            
            # Also check RMS energy as backup
            rms_energy = np.sqrt(np.mean(frame ** 2))
            energy_speech = rms_energy > self.silence_threshold
            
            return is_speech or energy_speech
            
        except Exception as e:
            logger.debug(f"VAD error: {e}")
            # Fallback to energy-based detection
            rms_energy = np.sqrt(np.mean(frame ** 2))
            return rms_energy > self.silence_threshold
    
    def _start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.recording_start_time = time.time()
        self.recording_buffer = []
        
        logger.debug("Started recording")
    
    def _stop_recording(self):
        """Stop recording and process audio"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        recording_duration = time.time() - self.recording_start_time
        
        logger.debug(f"Stopped recording ({recording_duration:.2f}s)")
        
        # Process the recorded audio
        if len(self.recording_buffer) > 0:
            audio_data = np.array(self.recording_buffer)
            asyncio.create_task(self._process_audio(audio_data))
        
        self.recording_buffer = []
    
    async def _process_audio(self, audio_data: np.ndarray):
        """Process recorded audio for transcription"""
        try:
            # Check minimum duration
            duration = len(audio_data) / self.sample_rate
            if duration < 0.5:  # Ignore very short recordings
                logger.debug(f"Ignoring short recording ({duration:.2f}s)")
                return
            
            logger.info(f"Processing audio ({duration:.2f}s, {len(audio_data)} samples)")
            
            # Call transcription callback if provided
            if self.transcription_callback:
                await self.transcription_callback(audio_data, self.sample_rate)
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
    
    def force_stop_recording(self):
        """Force stop current recording (hush word functionality)"""
        if self.is_recording:
            logger.info("Force stopping recording (hush word detected)")
            self._stop_recording()
    
    def toggle_push_to_talk(self):
        """Toggle push-to-talk mode"""
        self.push_to_talk = not self.push_to_talk
        logger.info(f"Push-to-talk mode: {'enabled' if self.push_to_talk else 'disabled'}")
    
    def get_status(self) -> dict:
        """Get current status of voice processor"""
        return {
            "listening": self.is_listening,
            "recording": self.is_recording,
            "push_to_talk": self.push_to_talk,
            "continuous_mode": self.continuous_mode,
            "sample_rate": self.sample_rate,
            "buffer_size": len(self.audio_buffer),
            "recording_duration": time.time() - self.recording_start_time if self.is_recording else 0
        }