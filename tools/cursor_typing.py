#!/usr/bin/env python3
"""
Cursor Typing Tool for Voxtral Agent
Types text at the current cursor position using Wayland tools
"""

import subprocess
import logging
import time
import os
from typing import Dict, Any
from langchain.tools import tool

logger = logging.getLogger(__name__)

def check_wayland_tools():
    """Check if required Wayland tools are available"""
    tools = ['wtype', 'wl-copy']
    missing = []
    
    for tool in tools:
        try:
            subprocess.run(['which', tool], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing.append(tool)
    
    return missing

@tool
def type_text(text: str, delay: float = 0.1) -> str:
    """
    Type text at the current cursor position.
    
    Args:
        text: The text to type
        delay: Delay between characters in seconds (default: 0.1)
        
    Returns:
        Success or error message
    """
    try:
        if not text:
            return "Error: No text provided to type"
        
        # Check if we're on Wayland
        if os.environ.get('WAYLAND_DISPLAY'):
            return _type_text_wayland(text, delay)
        elif os.environ.get('DISPLAY'):
            return _type_text_x11(text, delay)
        else:
            return "Error: No display server detected (neither Wayland nor X11)"
            
    except Exception as e:
        logger.error(f"Text typing error: {e}")
        return f"Error typing text: {str(e)}"

def _type_text_wayland(text: str, delay: float) -> str:
    """Type text using Wayland tools (clipboard+paste method for GNOME compatibility)"""
    try:
        # For GNOME Wayland, the most reliable method is clipboard + paste
        # This works around the virtual keyboard protocol limitations
        
        # Method 1: Try clipboard + paste (most reliable for GNOME Wayland)
        try:
            # Copy text to clipboard
            proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=text, timeout=5)
            
            if proc.returncode == 0:
                # Small delay to ensure clipboard is ready
                time.sleep(0.1)
                
                # Try to paste using keyboard shortcut simulation
                # First try with ydotool if available and working
                try:
                    result = subprocess.run(['ydotool', 'key', 'ctrl+v'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return f"Successfully pasted {len(text)} characters using ydotool"
                except:
                    pass
                
                # If ydotool fails, try wtype for key combination
                try:
                    result = subprocess.run(['wtype', '-M', 'ctrl', 'v'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return f"Successfully pasted {len(text)} characters using wtype"
                except:
                    pass
                
                # If both fail, at least the text is in clipboard
                return f"✅ Text ready to paste! Press Ctrl+V at your cursor position. ({len(text)} chars in clipboard)"
            
        except Exception as e:
            logger.warning(f"Clipboard method failed: {e}")
        
        # Method 2: Try direct typing with ydotool (if daemon is running)
        try:
            subprocess.run(['which', 'ydotool'], check=True, capture_output=True)
            result = subprocess.run(['ydotool', 'type', text], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return f"Successfully typed {len(text)} characters using ydotool"
            else:
                logger.warning(f"ydotool direct typing failed: {result.stderr}")
                
        except subprocess.CalledProcessError:
            logger.info("ydotool not available")
        
        # Method 3: Try wtype (likely to fail on GNOME but worth trying)
        missing_tools = check_wayland_tools()
        if 'wtype' not in missing_tools:
            cmd = ['wtype', text]
            if delay > 0:
                cmd.extend(['-d', str(int(delay * 1000))])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return f"Successfully typed {len(text)} characters using wtype"
            else:
                logger.warning(f"wtype failed: {result.stderr}")
        
        return "Error: All typing methods failed. GNOME Wayland has limited virtual keyboard support. Text may be in clipboard - try Ctrl+V"
            
    except subprocess.TimeoutExpired:
        return "Error: Typing operation timed out"
    except Exception as e:
        return f"Error with Wayland typing: {str(e)}"

def _type_text_x11(text: str, delay: float) -> str:
    """Type text using X11 tools (xdotool)"""
    try:
        # Check if xdotool is available
        try:
            subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            return "Error: xdotool not installed. Run: sudo apt install xdotool"
        
        # Use xdotool to type text
        cmd = ['xdotool', 'type', '--clearmodifiers']
        
        if delay > 0:
            cmd.extend(['--delay', str(int(delay * 1000))])
        
        cmd.append(text)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return f"Successfully typed {len(text)} characters"
        else:
            return f"Error: xdotool failed - {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return "Error: Typing operation timed out"
    except Exception as e:
        return f"Error with X11 typing: {str(e)}"

@tool
def paste_text(text: str) -> str:
    """
    Copy text to clipboard and paste it at cursor position.
    
    Args:
        text: The text to paste
        
    Returns:
        Success or error message
    """
    try:
        if not text:
            return "Error: No text provided to paste"
        
        if os.environ.get('WAYLAND_DISPLAY'):
            return _paste_text_wayland(text)
        elif os.environ.get('DISPLAY'):
            return _paste_text_x11(text)
        else:
            return "Error: No display server detected"
            
    except Exception as e:
        logger.error(f"Text pasting error: {e}")
        return f"Error pasting text: {str(e)}"

def _paste_text_wayland(text: str) -> str:
    """Paste text using Wayland clipboard"""
    try:
        # Copy to clipboard using wl-copy
        proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=text)
        
        if proc.returncode != 0:
            return "Error: Failed to copy to clipboard"
        
        # Simulate Ctrl+V using wtype
        time.sleep(0.1)  # Small delay
        result = subprocess.run(['wtype', '-M', 'ctrl', 'v'], capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Successfully pasted {len(text)} characters"
        else:
            return f"Error: Failed to paste - {result.stderr}"
            
    except Exception as e:
        return f"Error with Wayland pasting: {str(e)}"

def _paste_text_x11(text: str) -> str:
    """Paste text using X11 clipboard"""
    try:
        # Copy to clipboard using xclip
        proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=text)
        
        if proc.returncode != 0:
            return "Error: Failed to copy to clipboard (xclip not installed?)"
        
        # Simulate Ctrl+V using xdotool
        time.sleep(0.1)
        result = subprocess.run(['xdotool', 'key', 'ctrl+v'], capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Successfully pasted {len(text)} characters"
        else:
            return f"Error: Failed to paste - {result.stderr}"
            
    except Exception as e:
        return f"Error with X11 pasting: {str(e)}"

@tool
def open_url(url: str) -> str:
    """
    Open a URL in the default browser.
    
    Args:
        url: The URL to open
        
    Returns:
        Success or error message
    """
    try:
        if not url:
            return "Error: No URL provided"
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'https://' + url
        
        # Use xdg-open to open URL in default browser
        result = subprocess.run(['xdg-open', url], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return f"Successfully opened URL: {url}"
        else:
            return f"Error opening URL: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return "Error: URL opening timed out"
    except Exception as e:
        logger.error(f"URL opening error: {e}")
        return f"Error opening URL: {str(e)}"

def get_typing_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """Get schemas for all typing tools"""
    return {
        "type_text": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to type at cursor position"
                },
                "delay": {
                    "type": "number",
                    "description": "Delay between characters in seconds",
                    "minimum": 0,
                    "maximum": 1,
                    "default": 0.1
                }
            },
            "required": ["text"]
        },
        "paste_text": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to paste at cursor position"
                }
            },
            "required": ["text"]
        },
        "open_url": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to open in default browser"
                }
            },
            "required": ["url"]
        }
    }