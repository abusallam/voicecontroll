#!/usr/bin/env python3
"""
Voxtral Configuration Management
Handles all system settings, model configs, and environment setup
Enhanced with production-ready error handling from previous voice-control system
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil

class SimpleConfig:
    """Simple configuration class that works as a dictionary-like object"""
    
    def __init__(self, config_path: str = "config/voxtral.yaml"):
        self.config_path = config_path
        self.data = self._load_config()
        
        # Create user config directory for production use
        self.user_config_dir = Path.home() / ".local/share/voxtral"
        self.user_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        self.logs_dir = self.user_config_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.warning(f"Failed to load config from {self.config_path}: {e}")
                return self._get_default_config()
        else:
            logging.info(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "vllm_endpoint": "http://localhost:8000/v1",
            "model_name": "mistralai/Voxtral-Mini-3B-2507",
            "voice": {
                "sample_rate": 16000,
                "chunk_size": 1024,
                "channels": 1,
                "hush_word": "__stop__",
                "silence_threshold": 0.01,
                "silence_duration": 2.0,
                "push_to_talk": False,
                "continuous_mode": True
            },
            "model": {
                "temperature_transcription": 0.0,
                "temperature_chat": 0.2,
                "top_p": 0.95,
                "max_tokens": 2048,
                "gpu_memory_utilization": 0.8,
                "tensor_parallel_size": 1,
                "enable_tool_use": True,
                "tokenizer_mode": "mistral",
                "config_format": "mistral",
                "load_format": "mistral"
            },
            "system": {
                "os_type": "linux",
                "desktop_environment": "gnome",
                "display_server": "wayland",
                "audio_backend": "pulseaudio",
                "cursor_injection": True,
                "restart_services": ["pulseaudio", "pipewire", "seatd"],
                "logout_required": False
            },
            "tool_list": [
                {"name": "run_shell", "description": "Run safe shell commands"},
                {"name": "search_web", "description": "Search web with DuckDuckGo API"},
                {"name": "open_url", "description": "Open webpage in default browser"},
                {"name": "type_text", "description": "Type text at cursor position"}
            ],
            "tray_theme": "dark",
            "auto_start_agent": True,
            "debug": False,
            "log_level": "INFO"
        }
    
    def get(self, key: str, default=None):
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self.data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value with dot notation support"""
        keys = key.split('.')
        data = self.data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
    
    def save_config(self):
        """Save configuration to YAML file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config to {self.config_path}: {e}")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self.get("log_level", "INFO")
        debug = self.get("debug", False)
        
        if debug:
            log_level = "DEBUG"
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('voxtral.log'),
                logging.StreamHandler()
            ]
        )
        
        # Set specific logger levels
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)

# Global config instance
config = SimpleConfig()