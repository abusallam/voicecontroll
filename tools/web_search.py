#!/usr/bin/env python3
"""
Web Search Tool for Voxtral Agent
Searches the web using DuckDuckGo API
"""

import logging
import asyncio
from typing import Dict, Any, List
from langchain.tools import tool
from ddgs import DDGS

logger = logging.getLogger(__name__)

@tool
def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        Formatted search results
    """
    try:
        if not query.strip():
            return "Error: Empty search query"
        
        # Limit max_results to prevent spam
        max_results = min(max_results, 10)
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return f"No search results found for: {query}"
        
        # Format results
        formatted_results = f"Search results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No description')
            href = result.get('href', 'No URL')
            
            # Truncate long descriptions
            if len(body) > 200:
                body = body[:200] + "..."
            
            formatted_results += f"{i}. {title}\n"
            formatted_results += f"   {body}\n"
            formatted_results += f"   URL: {href}\n\n"
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Error searching the web: {str(e)}"

@tool
def search_news(query: str, max_results: int = 3) -> str:
    """
    Search for news using DuckDuckGo.
    
    Args:
        query: News search query
        max_results: Maximum number of news results (default: 3)
        
    Returns:
        Formatted news results
    """
    try:
        if not query.strip():
            return "Error: Empty news query"
        
        max_results = min(max_results, 5)
        
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
        
        if not results:
            return f"No news results found for: {query}"
        
        formatted_results = f"News results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No description')
            url = result.get('url', 'No URL')
            date = result.get('date', 'No date')
            source = result.get('source', 'Unknown source')
            
            if len(body) > 150:
                body = body[:150] + "..."
            
            formatted_results += f"{i}. {title}\n"
            formatted_results += f"   {body}\n"
            formatted_results += f"   Source: {source} | Date: {date}\n"
            formatted_results += f"   URL: {url}\n\n"
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"News search error: {e}")
        return f"Error searching news: {str(e)}"

def get_web_search_tool_schema() -> Dict[str, Any]:
    """Get the schema for the web search tool"""
    return {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (1-10)",
                "minimum": 1,
                "maximum": 10,
                "default": 5
            }
        },
        "required": ["query"]
    }

def get_news_search_tool_schema() -> Dict[str, Any]:
    """Get the schema for the news search tool"""
    return {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The news search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of news results (1-5)",
                "minimum": 1,
                "maximum": 5,
                "default": 3
            }
        },
        "required": ["query"]
    }