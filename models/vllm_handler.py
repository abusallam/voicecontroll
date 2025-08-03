#!/usr/bin/env python3
"""
VLLM Model Handler for Voxtral
Manages audio transcription and chat completion via OpenAI-compatible API
Includes fallback to OpenAI Whisper for transcription and CPU-only VLLM support
"""

import asyncio
import logging
import json
import aiohttp
import numpy as np
import subprocess
import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import tempfile
import soundfile as sf
from config.settings import config

logger = logging.getLogger(__name__)

# Try to import OpenAI Whisper as fallback
try:
    import whisper
    WHISPER_AVAILABLE = True
    logger.info("OpenAI Whisper available as fallback")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("OpenAI Whisper not available - transcription will rely on VLLM only")

class VLLMHandler:
    """Handles VLLM model operations via OpenAI-compatible API with audio transcription and tool support"""
    
    def __init__(self):
        self.endpoint = config.get("vllm_endpoint", "http://localhost:8000/v1")
        self.model_name = config.get("model_name", "mistralai/Voxtral-Mini-3B-2507")
        self.tools_registry = {}
        self.session = None
        
    async def initialize(self):
        """Initialize the HTTP session for API calls"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connection
            await self._test_connection()
            logger.info(f"VLLM API connection established: {self.endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize VLLM API connection: {e}")
            raise
    
    async def _test_connection(self):
        """Test if VLLM server is running"""
        try:
            async with self.session.get(f"{self.endpoint}/models") as response:
                if response.status == 200:
                    models = await response.json()
                    logger.info(f"Available models: {[m['id'] for m in models.get('data', [])]}")
                else:
                    raise Exception(f"Server returned status {response.status}")
        except Exception as e:
            raise Exception(f"VLLM server not accessible at {self.endpoint}: {e}")
    
    def register_tool(self, name: str, func: callable, description: str, parameters: Dict[str, Any]):
        """Register a tool for the model to use"""
        self.tools_registry[name] = {
            "function": func,
            "description": description,
            "parameters": parameters
        }
        logger.info(f"Registered tool: {name}")
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible tools schema"""
        tools = []
        for name, tool in self.tools_registry.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return tools
    
    async def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio using Voxtral via OpenAI-compatible API with Whisper fallback"""
        # First try VLLM transcription
        vllm_result = await self._transcribe_with_vllm(audio_data, sample_rate)
        if vllm_result:
            return vllm_result
        
        # Fallback to OpenAI Whisper if available
        if WHISPER_AVAILABLE:
            logger.info("VLLM transcription failed, falling back to OpenAI Whisper")
            return await self._transcribe_with_whisper(audio_data, sample_rate)
        
        logger.error("Both VLLM and Whisper transcription failed")
        return ""
    
    async def _transcribe_with_vllm(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio using VLLM/Voxtral"""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, sample_rate)
                temp_path = temp_file.name
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('file', open(temp_path, 'rb'), filename='audio.wav', content_type='audio/wav')
            data.add_field('model', self.model_name)
            data.add_field('temperature', str(config.get("model", {}).get("temperature_transcription", 0.0)))
            
            async with self.session.post(f"{self.endpoint}/audio/transcriptions", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    transcript = result.get("text", "")
                    logger.debug(f"VLLM Transcription: {transcript}")
                    return transcript
                else:
                    error_text = await response.text()
                    logger.warning(f"VLLM transcription failed: {response.status} - {error_text}")
                    return ""
                    
        except Exception as e:
            logger.warning(f"VLLM transcription error: {e}")
            return ""
        finally:
            # Clean up temp file
            try:
                Path(temp_path).unlink()
            except:
                pass
    
    async def _transcribe_with_whisper(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio using OpenAI Whisper as fallback"""
        if not WHISPER_AVAILABLE:
            return ""
        
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, sample_rate)
                temp_path = temp_file.name
            
            # Load Whisper model (use base model for speed)
            model = whisper.load_model("base")
            
            # Transcribe
            result = model.transcribe(temp_path, language="en")
            transcript = result["text"].strip()
            
            logger.debug(f"Whisper Transcription: {transcript}")
            return transcript
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""
        finally:
            # Clean up temp file
            try:
                Path(temp_path).unlink()
            except:
                pass
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """Generate chat completion with optional tool calling"""
        
        if not self.session:
            await self.initialize()
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": self._format_messages_for_api(messages, tools),
            "temperature": config.get("model", {}).get("temperature_chat", 0.2),
            "top_p": config.get("model", {}).get("top_p", 0.95),
            "max_tokens": config.get("model", {}).get("max_tokens", 2048),
            "stream": stream
        }
        
        # Add tools if provided
        if tools and config.get("model", {}).get("enable_tool_use", True):
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            async with self.session.post(
                f"{self.endpoint}/chat/completions", 
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    if stream:
                        return await self._handle_stream_response(response)
                    else:
                        result = await response.json()
                        return await self._handle_completion_response(result)
                else:
                    error_text = await response.text()
                    logger.error(f"Chat completion failed: {response.status} - {error_text}")
                    return f"Error: {error_text}"
                    
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            return f"Error: {str(e)}"
    
    def _format_messages_for_api(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
        """Format messages for OpenAI-compatible API"""
        
        # System message with Linux context and tool information
        system_content = """You are Voxtral, a voice-controlled AI assistant running on Linux (Debian 12 GNOME Wayland).

You help users with:
- Voice-to-text transcription and typing
- Shell commands and system operations
- Web searches and information lookup
- File operations and text editing
- General productivity tasks

You are cursor-aware and can type text directly where the user's cursor is positioned.
Be concise and helpful. When using tools, explain what you're doing briefly."""

        if tools:
            system_content += "\n\nAvailable tools:\n"
            for tool in tools:
                func_info = tool.get("function", {})
                system_content += f"- {func_info.get('name', 'unknown')}: {func_info.get('description', 'No description')}\n"
        
        formatted_messages = [{"role": "system", "content": system_content}]
        formatted_messages.extend(messages)
        
        return formatted_messages
    
    async def _handle_completion_response(self, result: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Handle non-streaming completion response"""
        try:
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            
            # Check for tool calls
            if "tool_calls" in message and message["tool_calls"]:
                return await self._execute_tool_calls(message["tool_calls"])
            
            # Regular text response
            return message.get("content", "No response generated")
            
        except Exception as e:
            logger.error(f"Error handling completion response: {e}")
            return f"Error processing response: {str(e)}"
    
    async def _handle_stream_response(self, response) -> str:
        """Handle streaming completion response"""
        full_response = ""
        tool_calls = []
        
        try:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        choice = chunk.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        
                        if "content" in delta and delta["content"]:
                            full_response += delta["content"]
                        
                        if "tool_calls" in delta:
                            tool_calls.extend(delta["tool_calls"])
                            
                    except json.JSONDecodeError:
                        continue
            
            # Execute tool calls if present
            if tool_calls:
                return await self._execute_tool_calls(tool_calls)
            
            return full_response
            
        except Exception as e:
            logger.error(f"Error handling stream response: {e}")
            return f"Error processing stream: {str(e)}"
    
    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Execute tool calls and return results"""
        results = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call.get("function", {}).get("name")
                arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                
                if function_name in self.tools_registry:
                    tool_func = self.tools_registry[function_name]["function"]
                    
                    if asyncio.iscoroutinefunction(tool_func):
                        result = await tool_func(**arguments)
                    else:
                        result = tool_func(**arguments)
                    
                    results.append(f"Tool '{function_name}' executed: {result}")
                    logger.info(f"Executed tool {function_name} with result: {result}")
                else:
                    results.append(f"Tool '{function_name}' not found")
                    logger.warning(f"Tool {function_name} not registered")
                    
            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                results.append(error_msg)
                logger.error(f"Tool execution error: {e}")
        
        return "\n".join(results) if results else "No tool results"
    
    async def shutdown(self):
        """Shutdown the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("VLLM handler shutdown")

# Global VLLM handler instance
vllm_handler = VLLMHandler()