#!/usr/bin/env python3
"""
Mock VLLM Server for Testing
Provides a simple HTTP server that mimics VLLM's OpenAI-compatible API
"""

import asyncio
import json
import logging
from typing import Dict, Any
from aiohttp import web, MultipartReader
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockVLLMServer:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get("/v1/models", self.list_models)
        self.app.router.add_post("/v1/chat/completions", self.chat_completions)
        self.app.router.add_post("/v1/audio/transcriptions", self.audio_transcriptions)
        self.app.router.add_get("/health", self.health_check)
    
    async def list_models(self, request):
        """List available models"""
        return web.json_response({
            "object": "list",
            "data": [
                {
                    "id": "mistralai/Voxtral-Mini-3B-2507",
                    "object": "model",
                    "created": 1234567890,
                    "owned_by": "mistralai"
                }
            ]
        })
    
    async def chat_completions(self, request):
        """Handle chat completions"""
        try:
            data = await request.json()
            messages = data.get("messages", [])
            tools = data.get("tools", [])
            
            # Get the last user message
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            # Simple response generation based on content
            response_content = self._generate_mock_response(user_message, tools)
            
            # Check if this should be a tool call
            tool_calls = None
            if tools and self._should_use_tool(user_message):
                tool_calls = self._generate_tool_call(user_message, tools)
                response_content = ""
            
            response = {
                "id": "chatcmpl-mock123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "mistralai/Voxtral-Mini-3B-2507",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content,
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 20,
                    "total_tokens": 70
                }
            }
            
            if tool_calls:
                response["choices"][0]["message"]["tool_calls"] = tool_calls
                response["choices"][0]["finish_reason"] = "tool_calls"
            
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            return web.json_response(
                {"error": {"message": str(e), "type": "server_error"}},
                status=500
            )
    
    async def audio_transcriptions(self, request):
        """Handle audio transcriptions"""
        try:
            # Read multipart form data
            reader = MultipartReader.from_response(request)
            
            audio_file = None
            model = "mistralai/Voxtral-Mini-3B-2507"
            temperature = 0.0
            
            async for part in reader:
                if part.name == 'file':
                    # Save audio file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                        async for chunk in part:
                            tmp.write(chunk)
                        audio_file = tmp.name
                elif part.name == 'model':
                    model = (await part.text()).strip()
                elif part.name == 'temperature':
                    temperature = float((await part.text()).strip())
            
            if not audio_file:
                return web.json_response(
                    {"error": {"message": "No audio file provided", "type": "invalid_request"}},
                    status=400
                )
            
            # Mock transcription - in reality this would process the audio
            # For testing, we'll return a simple mock transcription
            mock_transcription = "Hello, this is a test transcription from the mock server."
            
            # Clean up temp file
            try:
                os.unlink(audio_file)
            except:
                pass
            
            return web.json_response({
                "text": mock_transcription
            })
            
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return web.json_response(
                {"error": {"message": str(e), "type": "server_error"}},
                status=500
            )
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({"status": "healthy"})
    
    def _generate_mock_response(self, user_message: str, tools: list) -> str:
        """Generate a mock response based on user input"""
        user_lower = user_message.lower()
        
        if "hello" in user_lower or "hi" in user_lower:
            return "Hello! I'm the Voxtral mock server. How can I help you today?"
        elif "type" in user_lower:
            return "I'll help you type that text."
        elif "search" in user_lower:
            return "I'll search for that information."
        elif "run" in user_lower or "execute" in user_lower:
            return "I'll execute that command safely."
        else:
            return f"I understand you said: '{user_message}'. How can I assist you?"
    
    def _should_use_tool(self, user_message: str) -> bool:
        """Determine if a tool should be used"""
        user_lower = user_message.lower()
        tool_keywords = ["type", "search", "run", "execute", "open", "find"]
        return any(keyword in user_lower for keyword in tool_keywords)
    
    def _generate_tool_call(self, user_message: str, tools: list) -> list:
        """Generate a mock tool call"""
        user_lower = user_message.lower()
        
        if "type" in user_lower and tools:
            # Find type_text tool
            for tool in tools:
                if tool.get("function", {}).get("name") == "type_text":
                    return [{
                        "id": "call_mock123",
                        "type": "function",
                        "function": {
                            "name": "type_text",
                            "arguments": json.dumps({"text": "Hello from mock server!"})
                        }
                    }]
        
        elif "search" in user_lower and tools:
            # Find search tool
            for tool in tools:
                if "search" in tool.get("function", {}).get("name", ""):
                    return [{
                        "id": "call_mock124",
                        "type": "function",
                        "function": {
                            "name": tool["function"]["name"],
                            "arguments": json.dumps({"query": "test search"})
                        }
                    }]
        
        elif "run" in user_lower and tools:
            # Find shell tool
            for tool in tools:
                if tool.get("function", {}).get("name") == "run_shell":
                    return [{
                        "id": "call_mock125",
                        "type": "function",
                        "function": {
                            "name": "run_shell",
                            "arguments": json.dumps({"command": "echo 'mock command'"})
                        }
                    }]
        
        return []
    
    async def start(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Mock VLLM server started on http://{self.host}:{self.port}")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down mock server...")
        finally:
            await runner.cleanup()

async def main():
    server = MockVLLMServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())