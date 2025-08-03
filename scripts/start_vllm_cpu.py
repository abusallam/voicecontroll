#!/usr/bin/env python3
"""
CPU-only VLLM Server Starter
Attempts to start VLLM with CPU-only configuration for systems without GPU
"""

import subprocess
import sys
import os
import time
import logging
import signal
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_gpu_availability():
    """Check if GPU is available for VLLM"""
    try:
        # Check for NVIDIA GPU
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("NVIDIA GPU detected")
            return "cuda"
    except FileNotFoundError:
        pass
    
    try:
        # Check for AMD GPU
        result = subprocess.run(['rocm-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("AMD GPU detected")
            return "rocm"
    except FileNotFoundError:
        pass
    
    logger.info("No GPU detected, will use CPU-only mode")
    return "cpu"

def start_vllm_server(device_type="cpu", port=8000):
    """Start VLLM server with appropriate device configuration"""
    
    model_name = "mistralai/Voxtral-Mini-3B-2507"
    
    # Base command
    cmd = [
        "vllm", "serve", model_name,
        "--host", "0.0.0.0",
        "--port", str(port),
        "--tokenizer_mode", "mistral",
        "--config_format", "mistral",
        "--load_format", "mistral"
    ]
    
    # Add device-specific arguments
    if device_type == "cpu":
        cmd.extend([
            "--device", "cpu",
            "--dtype", "float32",  # CPU works better with float32
            "--max_model_len", "2048",  # Reduce for CPU
            "--disable_log_stats",
            "--enforce_eager"  # Disable CUDA graphs for CPU
        ])
        logger.info("Starting VLLM with CPU-only configuration")
    elif device_type == "cuda":
        cmd.extend([
            "--device", "cuda",
            "--dtype", "auto",
            "--gpu_memory_utilization", "0.8"
        ])
        logger.info("Starting VLLM with CUDA GPU configuration")
    elif device_type == "rocm":
        cmd.extend([
            "--device", "cuda",  # ROCm uses CUDA API
            "--dtype", "auto"
        ])
        logger.info("Starting VLLM with ROCm GPU configuration")
    
    # Set environment variables for CPU mode
    env = os.environ.copy()
    if device_type == "cpu":
        env.update({
            "VLLM_CPU_KVCACHE_SPACE": "4",  # Limit KV cache for CPU
            "VLLM_LOGGING_LEVEL": "INFO",
            "OMP_NUM_THREADS": "4"  # Limit OpenMP threads
        })
    
    try:
        logger.info(f"Executing command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, env=env)
        
        # Wait a bit to see if it starts successfully
        time.sleep(5)
        
        if process.poll() is None:
            logger.info(f"VLLM server started successfully (PID: {process.pid})")
            return process
        else:
            logger.error("VLLM server failed to start")
            return None
            
    except Exception as e:
        logger.error(f"Failed to start VLLM server: {e}")
        return None

def main():
    """Main function to start VLLM server with fallback options"""
    
    # Check device availability
    device_type = check_gpu_availability()
    
    # Try to start VLLM server
    process = start_vllm_server(device_type)
    
    if not process:
        if device_type != "cpu":
            logger.info("GPU mode failed, trying CPU-only mode...")
            process = start_vllm_server("cpu")
        
        if not process:
            logger.error("Failed to start VLLM server in any mode")
            sys.exit(1)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down VLLM server...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("VLLM server didn't shut down gracefully, forcing kill")
            process.kill()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("VLLM server is running. Press Ctrl+C to stop.")
    
    try:
        # Wait for the process to complete
        process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()