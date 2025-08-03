#!/usr/bin/env python3
"""
LangGraph Workflows for Voxtral Agent
Orchestrates agent behavior, tool usage, and conversation flow
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from models.vllm_handler import vllm_handler
from tools.shell import run_shell, get_shell_tool_schema
from tools.web_search import search_web, search_news, get_web_search_tool_schema, get_news_search_tool_schema
from tools.cursor_typing import type_text, paste_text, open_url, get_typing_tool_schemas
from config.settings import config

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the Voxtral agent workflow"""
    messages: Annotated[List, add_messages]
    transcript: str
    context: Dict[str, Any]
    tools_used: List[str]
    response: str
    should_type: bool

class VoxtralWorkflow:
    """Main workflow orchestrator for Voxtral agent"""
    
    def __init__(self):
        self.graph = None
        self.tools_registry = {}
        self._setup_tools()
        self._build_graph()
    
    def _setup_tools(self):
        """Register all available tools"""
        # Register tools with VLLM handler
        vllm_handler.register_tool("run_shell", run_shell, 
                                  "Execute safe shell commands on Linux", 
                                  get_shell_tool_schema())
        
        vllm_handler.register_tool("search_web", search_web,
                                  "Search the web using DuckDuckGo",
                                  get_web_search_tool_schema())
        
        vllm_handler.register_tool("search_news", search_news,
                                  "Search for news using DuckDuckGo",
                                  get_news_search_tool_schema())
        
        typing_schemas = get_typing_tool_schemas()
        vllm_handler.register_tool("type_text", type_text,
                                  "Type text at the current cursor position",
                                  typing_schemas["type_text"])
        
        vllm_handler.register_tool("paste_text", paste_text,
                                  "Paste text at the current cursor position",
                                  typing_schemas["paste_text"])
        
        vllm_handler.register_tool("open_url", open_url,
                                  "Open a URL in the default browser",
                                  typing_schemas["open_url"])
        
        logger.info("All tools registered with VLLM handler")
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("process_input", self._process_input_node)
        workflow.add_node("agent_reasoning", self._agent_reasoning_node)
        workflow.add_node("execute_tools", self._execute_tools_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("output_handler", self._output_handler_node)
        
        # Define edges
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "agent_reasoning")
        workflow.add_conditional_edges(
            "agent_reasoning",
            self._should_use_tools,
            {
                "use_tools": "execute_tools",
                "generate_response": "generate_response"
            }
        )
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", "output_handler")
        workflow.add_edge("output_handler", END)
        
        self.graph = workflow.compile()
        logger.info("LangGraph workflow compiled successfully")
    
    async def _process_input_node(self, state: AgentState) -> AgentState:
        """Process the input transcript and prepare context"""
        try:
            transcript = state.get("transcript", "").strip()
            
            if not transcript:
                logger.warning("Empty transcript received")
                return {**state, "response": "I didn't hear anything. Could you please repeat?"}
            
            logger.info(f"Processing transcript: {transcript}")
            
            # Detect if this is a command or natural speech
            context = self._analyze_context(transcript)
            
            # Initialize messages if not present
            if "messages" not in state:
                state["messages"] = []
            
            # Add user message
            state["messages"].append(HumanMessage(content=transcript))
            
            return {
                **state,
                "transcript": transcript,
                "context": context,
                "tools_used": [],
                "should_type": context.get("should_type", True)
            }
            
        except Exception as e:
            logger.error(f"Input processing error: {e}")
            return {**state, "response": f"Error processing input: {str(e)}"}
    
    def _analyze_context(self, transcript: str) -> Dict[str, Any]:
        """Analyze transcript context to determine appropriate response"""
        transcript_lower = transcript.lower()
        
        context = {
            "should_type": True,
            "is_command": False,
            "intent": "general",
            "urgency": "normal"
        }
        
        # Detect commands
        command_indicators = [
            "run", "execute", "search", "find", "open", "type", "paste",
            "show me", "tell me", "what is", "how to", "help me"
        ]
        
        if any(indicator in transcript_lower for indicator in command_indicators):
            context["is_command"] = True
            context["should_type"] = False  # Commands usually don't need typing
        
        # Detect typing intent
        typing_indicators = [
            "type", "write", "insert", "add", "put", "enter"
        ]
        
        if any(indicator in transcript_lower for indicator in typing_indicators):
            context["intent"] = "typing"
            context["should_type"] = True
        
        # Detect search intent
        search_indicators = [
            "search", "find", "look up", "google", "what is", "who is"
        ]
        
        if any(indicator in transcript_lower for indicator in search_indicators):
            context["intent"] = "search"
            context["should_type"] = False
        
        return context
    
    async def _agent_reasoning_node(self, state: AgentState) -> AgentState:
        """Main agent reasoning with LLM"""
        try:
            messages = state.get("messages", [])
            context = state.get("context", {})
            
            # Get available tools
            tools = vllm_handler.get_tools_schema()
            
            # Generate response using VLLM
            response = await vllm_handler.chat_completion(
                messages=[{"role": msg.type, "content": msg.content} for msg in messages],
                tools=tools if context.get("is_command", False) else None
            )
            
            # Check if response contains tool usage
            if isinstance(response, dict) and "tool_calls" in str(response):
                state["needs_tools"] = True
            else:
                state["needs_tools"] = False
                state["response"] = str(response)
            
            return state
            
        except Exception as e:
            logger.error(f"Agent reasoning error: {e}")
            return {**state, "response": f"I encountered an error while thinking: {str(e)}"}
    
    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if tools should be used"""
        return "use_tools" if state.get("needs_tools", False) else "generate_response"
    
    async def _execute_tools_node(self, state: AgentState) -> AgentState:
        """Execute any required tools"""
        try:
            # Tool execution is handled within the VLLM handler
            # This node is for any additional tool coordination if needed
            logger.info("Tools executed via VLLM handler")
            return state
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {**state, "response": f"Error executing tools: {str(e)}"}
    
    async def _generate_response_node(self, state: AgentState) -> AgentState:
        """Generate final response"""
        try:
            if "response" not in state or not state["response"]:
                # Generate a response if we don't have one
                messages = state.get("messages", [])
                
                response = await vllm_handler.chat_completion(
                    messages=[{"role": msg.type, "content": msg.content} for msg in messages]
                )
                
                state["response"] = str(response)
            
            # Add AI message to conversation
            state["messages"].append(AIMessage(content=state["response"]))
            
            return state
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {**state, "response": f"Error generating response: {str(e)}"}
    
    async def _output_handler_node(self, state: AgentState) -> AgentState:
        """Handle output - typing, speaking, or just logging"""
        try:
            response = state.get("response", "")
            should_type = state.get("should_type", True)
            context = state.get("context", {})
            
            logger.info(f"Agent response: {response}")
            
            # If this is a typing intent and cursor injection is enabled
            if should_type and context.get("intent") == "typing" and config.get("system", {}).get("cursor_injection", True):
                # Extract text to type from response
                text_to_type = self._extract_text_to_type(response, state.get("transcript", ""))
                
                if text_to_type:
                    # Use the type_text tool
                    typing_result = type_text(text_to_type)
                    logger.info(f"Typing result: {typing_result}")
            
            return state
            
        except Exception as e:
            logger.error(f"Output handling error: {e}")
            return state
    
    def _extract_text_to_type(self, response: str, transcript: str) -> str:
        """Extract text that should be typed from the response"""
        # Simple heuristic: if the transcript contains "type" or "write"
        # and the response is not a tool execution result, type the response
        
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in ["type", "write", "insert", "add"]):
            # Remove common response prefixes
            prefixes_to_remove = [
                "I'll type:", "I'll write:", "Here's the text:", "Typing:",
                "I'll insert:", "I'll add:", "Here you go:", "Sure, I'll type:"
            ]
            
            text = response
            for prefix in prefixes_to_remove:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            
            return text
        
        return ""
    
    async def process_transcript(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a voice transcript through the workflow"""
        try:
            initial_state = {
                "transcript": transcript,
                "context": context or {},
                "messages": [],
                "tools_used": [],
                "response": "",
                "should_type": True
            }
            
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "response": final_state.get("response", ""),
                "tools_used": final_state.get("tools_used", []),
                "should_type": final_state.get("should_type", True),
                "context": final_state.get("context", {})
            }
            
        except Exception as e:
            logger.error(f"Workflow processing error: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "tools_used": [],
                "should_type": False,
                "context": {}
            }

# Global workflow instance
voxtral_workflow = VoxtralWorkflow()