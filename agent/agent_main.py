#!/usr/bin/env python3
"""
Main Voxtral Agent
Coordinates voice processing, transcription, and agent workflows
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
from typing import Optional
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config
from models.vllm_handler import vllm_handler
from agent.voice_processor import VoiceProcessor
from langraph.workflows import voxtral_workflow

# Setup logging
config.setup_logging()
logger = logging.getLogger(__name__)

class VoxtralAgent:
    """Main Voxtral Agent orchestrator"""
    
    def __init__(self):
        self.voice_processor = None
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing Voxtral Agent...")
            
            # Initialize VLLM handler
            await vllm_handler.initialize()
            
            # Initialize voice processor with transcription callback
            self.voice_processor = VoiceProcessor(transcription_callback=self._handle_transcription)
            
            logger.info("Voxtral Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def _handle_transcription(self, audio_data: np.ndarray, sample_rate: int):
        """Handle transcribed audio from voice processor"""
        try:
            logger.info("Processing audio transcription...")
            
            # Transcribe audio using VLLM
            transcript = await vllm_handler.transcribe_audio(audio_data, sample_rate)
            
            if not transcript.strip():
                logger.debug("Empty transcription, ignoring")
                return
            
            logger.info(f"Transcription: {transcript}")
            
            # Check for hush word
            hush_word = config.get("voice", {}).get("hush_word", "__stop__")
            if hush_word in transcript.lower():
                logger.info("Hush word detected, stopping recording")
                self.voice_processor.force_stop_recording()
                return
            
            # Process through LangGraph workflow
            result = await voxtral_workflow.process_transcript(transcript)
            
            logger.info(f"Agent response: {result['response']}")
            
            # Log tools used
            if result['tools_used']:
                logger.info(f"Tools used: {', '.join(result['tools_used'])}")
            
        except Exception as e:
            logger.error(f"Transcription handling error: {e}")
    
    async def start(self):
        """Start the agent"""
        if self.is_running:
            logger.warning("Agent is already running")
            return
        
        try:
            await self.initialize()
            
            self.is_running = True
            logger.info("Starting Voxtral Agent...")
            
            # Start voice processing
            self.voice_processor.start_listening()
            
            logger.info("Voxtral Agent is now listening for voice input")
            logger.info("Speak naturally - the agent will transcribe and respond")
            logger.info(f"Say '{config.get('voice', {}).get('hush_word', '__stop__')}' to stop current recording")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Agent startup error: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the agent"""
        if not self.is_running:
            return
        
        logger.info("Stopping Voxtral Agent...")
        
        self.is_running = False
        
        # Stop voice processor
        if self.voice_processor:
            self.voice_processor.stop_listening()
        
        # Shutdown VLLM handler
        await vllm_handler.shutdown()
        
        logger.info("Voxtral Agent stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_event.set()
    
    def get_status(self) -> dict:
        """Get current agent status"""
        status = {
            "running": self.is_running,
            "voice_processor": None,
            "vllm_handler": "initialized" if vllm_handler.session else "not_initialized"
        }
        
        if self.voice_processor:
            status["voice_processor"] = self.voice_processor.get_status()
        
        return status

async def main():
    """Main entry point"""
    agent = VoxtralAgent()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, agent.signal_handler)
    signal.signal(signal.SIGTERM, agent.signal_handler)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Agent error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if VLLM server is expected to be running
    vllm_endpoint = config.get("vllm_endpoint", "http://localhost:8000/v1")
    logger.info(f"Expecting VLLM server at: {vllm_endpoint}")
    logger.info("Make sure to start VLLM server first:")
    logger.info("vllm serve mistralai/Voxtral-Mini-3B-2507 --tokenizer_mode mistral --config_format mistral --load_format mistral")
    
    # Run the agent
    asyncio.run(main())