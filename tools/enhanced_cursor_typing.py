#!/usr/bin/env python3
"""
Enhanced Cursor Typing Tool for Voxtral Agent
Uses "hacker-style" tools for robust text injection on Wayland/X11
Implements multiple fallback methods for maximum compatibility
"""

import subprocess
import logging
import time
import os
import shutil
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
# Removed langchain dependency - using simple function decorators instead

logger = logging.getLogger(__name__)

@dataclass
class WindowInfo:
    """Information about the active window"""
    window_id: str
    title: str
    class_name: str
    process_name: str
    is_text_editor: bool
    cursor_position: Optional[Tuple[int, int]] = None

@dataclass
class TypingResult:
    """Result of a typing operation"""
    success: bool
    method_used: str
    characters_typed: int
    error_message: Optional[str] = None
    fallback_used: bool = False

class CursorTypingManager:
    """Enhanced cursor typing with multiple injection methods"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_tools = self._detect_available_tools()
        self.preferred_apps = ["code", "gedit", "kate", "sublime", "atom", "notepad", "vim", "nano"]
        
    def _detect_available_tools(self) -> Dict[str, bool]:
        """Detect which typing tools are available on the system"""
        tools = {
            'wtype': False,
            'ydotool': False,
            'xdotool': False,
            'wl-copy': False,
            'xclip': False,
            'interception-tools': False
        }
        
        for tool in tools.keys():
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                tools[tool] = result.returncode == 0
                if tools[tool]:
                    self.logger.debug(f"✅ {tool} available")
                else:
                    self.logger.debug(f"❌ {tool} not available")
            except:
                pass
                
        return tools
    
    def type_at_cursor(self, text: str, delay: float = 0.05) -> TypingResult:
        """
        Type text at cursor position using the best available method
        
        Args:
            text: Text to type
            delay: Delay between characters (for some methods)
            
        Returns:
            TypingResult with success status and method used
        """
        if not text.strip():
            return TypingResult(False, "none", 0, "No text provided")
        
        self.logger.info(f"🎯 Typing {len(text)} characters: {text[:50]}...")
        
        # Get window information for context-aware typing
        window_info = self.detect_active_window()
        
        # Try methods in order of preference and reliability
        methods = self._get_typing_methods()
        
        for method_name, method_func in methods:
            try:
                self.logger.debug(f"Trying method: {method_name}")
                result = method_func(text, delay, window_info)
                
                if result.success:
                    self.logger.info(f"✅ Success with {method_name}: {len(text)} chars")
                    return result
                else:
                    self.logger.warning(f"⚠️ {method_name} failed: {result.error_message}")
                    
            except Exception as e:
                self.logger.error(f"❌ {method_name} error: {e}")
                continue
        
        # All methods failed
        return TypingResult(False, "all_failed", 0, "All typing methods failed")
    
    def _get_typing_methods(self) -> list:
        """Get typing methods in order of preference"""
        methods = []
        
        # Method 1: wtype (best for Wayland)
        if self.available_tools.get('wtype') and os.environ.get('WAYLAND_DISPLAY'):
            methods.append(("wtype_direct", self._type_with_wtype))
        
        # Method 2: ydotool (powerful, works everywhere but needs setup)
        if self.available_tools.get('ydotool'):
            methods.append(("ydotool_direct", self._type_with_ydotool))
        
        # Method 3: xdotool (best for X11)
        if self.available_tools.get('xdotool') and os.environ.get('DISPLAY'):
            methods.append(("xdotool_direct", self._type_with_xdotool))
        
        # Method 4: Smart clipboard + paste (most compatible)
        methods.append(("smart_clipboard", self._type_with_smart_clipboard))
        
        # Method 5: Basic clipboard (fallback)
        methods.append(("basic_clipboard", self._type_with_basic_clipboard))
        
        return methods
    
    def _type_with_wtype(self, text: str, delay: float, window_info: WindowInfo) -> TypingResult:
        """Type using wtype (Wayland native)"""
        if not self.available_tools.get('wtype'):
            return TypingResult(False, "wtype", 0, "wtype not available")
        
        try:
            cmd = ['wtype']
            if delay > 0:
                cmd.extend(['-d', str(int(delay * 1000))])  # Convert to milliseconds
            cmd.append(text)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return TypingResult(True, "wtype", len(text))
            else:
                return TypingResult(False, "wtype", 0, f"wtype failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            return TypingResult(False, "wtype", 0, "wtype timeout")
        except Exception as e:
            return TypingResult(False, "wtype", 0, str(e))
    
    def _type_with_ydotool(self, text: str, delay: float, window_info: WindowInfo) -> TypingResult:
        """Type using ydotool with sudo (root-level injection)"""
        if not self.available_tools.get('ydotool'):
            return TypingResult(False, "ydotool", 0, "ydotool not available")
        
        try:
            # Use sudo ydotool directly (no daemon needed for newer versions)
            cmd = ['sudo', 'ydotool', 'type']
            if delay > 0:
                cmd.extend(['--delay', str(int(delay * 1000))])
            cmd.append(text)
            
            self.logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return TypingResult(True, "ydotool_sudo", len(text))
            else:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                return TypingResult(False, "ydotool_sudo", 0, f"ydotool failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            return TypingResult(False, "ydotool_sudo", 0, "ydotool timeout")
        except Exception as e:
            return TypingResult(False, "ydotool_sudo", 0, str(e))
    
    def _type_with_xdotool(self, text: str, delay: float, window_info: WindowInfo) -> TypingResult:
        """Type using xdotool (X11 native)"""
        if not self.available_tools.get('xdotool'):
            return TypingResult(False, "xdotool", 0, "xdotool not available")
        
        try:
            cmd = ['xdotool', 'type', '--clearmodifiers']
            if delay > 0:
                cmd.extend(['--delay', str(int(delay * 1000))])
            
            # If we have window info, target specific window
            if window_info and window_info.window_id:
                cmd.extend(['--window', window_info.window_id])
            
            cmd.append(text)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return TypingResult(True, "xdotool", len(text))
            else:
                return TypingResult(False, "xdotool", 0, f"xdotool failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            return TypingResult(False, "xdotool", 0, "xdotool timeout")
        except Exception as e:
            return TypingResult(False, "xdotool", 0, str(e))
    
    def _type_with_smart_clipboard(self, text: str, delay: float, window_info: WindowInfo) -> TypingResult:
        """Smart clipboard method with window targeting"""
        try:
            # Copy to clipboard
            clipboard_success = self._copy_to_clipboard(text)
            if not clipboard_success:
                return TypingResult(False, "smart_clipboard", 0, "Failed to copy to clipboard")
            
            time.sleep(0.1)  # Ensure clipboard is ready
            
            # Try to focus the right window if we have window info
            if window_info and window_info.window_id and self.available_tools.get('xdotool'):
                try:
                    subprocess.run(['xdotool', 'windowfocus', window_info.window_id], 
                                 capture_output=True, timeout=2)
                    time.sleep(0.1)
                except:
                    pass  # Continue even if focus fails
            
            # Paste using the best available method
            paste_success = self._paste_from_clipboard()
            
            if paste_success:
                return TypingResult(True, "smart_clipboard", len(text))
            else:
                # Text is in clipboard, user can paste manually
                return TypingResult(True, "smart_clipboard", len(text), 
                                  "Text ready in clipboard - press Ctrl+V to paste", 
                                  fallback_used=True)
                
        except Exception as e:
            return TypingResult(False, "smart_clipboard", 0, str(e))
    
    def _type_with_basic_clipboard(self, text: str, delay: float, window_info: WindowInfo) -> TypingResult:
        """Basic clipboard fallback"""
        try:
            clipboard_success = self._copy_to_clipboard(text)
            if clipboard_success:
                return TypingResult(True, "basic_clipboard", len(text), 
                                  "Text copied to clipboard - press Ctrl+V to paste", 
                                  fallback_used=True)
            else:
                return TypingResult(False, "basic_clipboard", 0, "Failed to copy to clipboard")
                
        except Exception as e:
            return TypingResult(False, "basic_clipboard", 0, str(e))
    
    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard using best available method"""
        try:
            if os.environ.get('WAYLAND_DISPLAY') and self.available_tools.get('wl-copy'):
                proc = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=5)
                return proc.returncode == 0
            
            elif os.environ.get('DISPLAY') and self.available_tools.get('xclip'):
                proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                      stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text, timeout=5)
                return proc.returncode == 0
            
            return False
            
        except Exception as e:
            self.logger.error(f"Clipboard copy error: {e}")
            return False
    
    def _paste_from_clipboard(self) -> bool:
        """Paste from clipboard using keyboard shortcut"""
        try:
            # Try different paste methods
            if os.environ.get('WAYLAND_DISPLAY'):
                if self.available_tools.get('ydotool'):
                    result = subprocess.run(['ydotool', 'key', 'ctrl+v'], 
                                          capture_output=True, timeout=3)
                    if result.returncode == 0:
                        return True
                
                if self.available_tools.get('wtype'):
                    result = subprocess.run(['wtype', '-M', 'ctrl', 'v'], 
                                          capture_output=True, timeout=3)
                    if result.returncode == 0:
                        return True
            
            elif os.environ.get('DISPLAY') and self.available_tools.get('xdotool'):
                result = subprocess.run(['xdotool', 'key', 'ctrl+v'], 
                                      capture_output=True, timeout=3)
                return result.returncode == 0
            
            return False
            
        except Exception as e:
            self.logger.error(f"Paste error: {e}")
            return False
    
    def detect_active_window(self) -> Optional[WindowInfo]:
        """Detect the currently active window"""
        try:
            if os.environ.get('DISPLAY') and self.available_tools.get('xdotool'):
                return self._detect_window_x11()
            elif os.environ.get('WAYLAND_DISPLAY'):
                return self._detect_window_wayland()
            
        except Exception as e:
            self.logger.error(f"Window detection error: {e}")
        
        return None
    
    def _detect_window_x11(self) -> Optional[WindowInfo]:
        """Detect active window on X11"""
        try:
            # Get active window ID
            result = subprocess.run(['xdotool', 'getactivewindow'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                return None
            
            window_id = result.stdout.strip()
            
            # Get window title
            title_result = subprocess.run(['xdotool', 'getwindowname', window_id], 
                                        capture_output=True, text=True, timeout=2)
            title = title_result.stdout.strip() if title_result.returncode == 0 else ""
            
            # Get window class
            class_result = subprocess.run(['xprop', '-id', window_id, 'WM_CLASS'], 
                                        capture_output=True, text=True, timeout=2)
            class_name = ""
            if class_result.returncode == 0:
                # Parse WM_CLASS output
                class_line = class_result.stdout.strip()
                if '"' in class_line:
                    class_name = class_line.split('"')[1]
            
            # Determine if it's a text editor
            is_text_editor = any(app.lower() in title.lower() or app.lower() in class_name.lower() 
                               for app in self.preferred_apps)
            
            return WindowInfo(
                window_id=window_id,
                title=title,
                class_name=class_name,
                process_name="",  # Could be enhanced
                is_text_editor=is_text_editor
            )
            
        except Exception as e:
            self.logger.error(f"X11 window detection error: {e}")
            return None
    
    def _detect_window_wayland(self) -> Optional[WindowInfo]:
        """Detect active window on Wayland (limited capabilities)"""
        # Wayland has limited window detection capabilities for security
        # We can try some heuristics but it's not as reliable as X11
        try:
            # Try to get focused application from GNOME Shell (if available)
            if shutil.which('gdbus'):
                result = subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest', 'org.gnome.Shell',
                    '--object-path', '/org/gnome/Shell',
                    '--method', 'org.gnome.Shell.Eval',
                    'global.display.focus_window.get_wm_class()'
                ], capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0 and 'true' in result.stdout:
                    # Parse the result to get window class
                    # This is a simplified approach
                    pass
            
            # For now, return a generic window info for Wayland
            return WindowInfo(
                window_id="wayland",
                title="Unknown",
                class_name="Unknown",
                process_name="",
                is_text_editor=False
            )
            
        except Exception as e:
            self.logger.error(f"Wayland window detection error: {e}")
            return None

# Create global instance
cursor_typing_manager = CursorTypingManager()

def type_text_enhanced(text: str, delay: float = 0.05) -> str:
    """
    Enhanced text typing at cursor position with multiple fallback methods.
    
    Args:
        text: The text to type
        delay: Delay between characters in seconds (default: 0.05)
        
    Returns:
        Success message with method used or error message
    """
    result = cursor_typing_manager.type_at_cursor(text, delay)
    
    if result.success:
        if result.fallback_used:
            return f"✅ {result.method_used}: {result.error_message or 'Text ready to paste'}"
        else:
            return f"✅ Successfully typed {result.characters_typed} characters using {result.method_used}"
    else:
        return f"❌ Failed to type text: {result.error_message}"

def get_typing_capabilities() -> str:
    """
    Get information about available typing methods and capabilities.
    
    Returns:
        String describing available typing tools and methods
    """
    tools = cursor_typing_manager.available_tools
    capabilities = []
    
    if tools.get('wtype'):
        capabilities.append("✅ wtype (Wayland native typing)")
    if tools.get('ydotool'):
        capabilities.append("✅ ydotool (root-level injection)")
    if tools.get('xdotool'):
        capabilities.append("✅ xdotool (X11 native typing)")
    if tools.get('wl-copy'):
        capabilities.append("✅ wl-copy (Wayland clipboard)")
    if tools.get('xclip'):
        capabilities.append("✅ xclip (X11 clipboard)")
    
    if not capabilities:
        capabilities.append("❌ No typing tools available")
    
    display_server = "Wayland" if os.environ.get('WAYLAND_DISPLAY') else "X11" if os.environ.get('DISPLAY') else "Unknown"
    
    return f"Display server: {display_server}\nAvailable tools:\n" + "\n".join(capabilities)

# Legacy compatibility
def type_text(text: str, delay: float = 0.1) -> str:
    """Legacy type_text function for backward compatibility"""
    return type_text_enhanced(text, delay)

def get_enhanced_typing_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """Get schemas for enhanced typing tools"""
    return {
        "type_text_enhanced": {
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
                    "default": 0.05
                }
            },
            "required": ["text"]
        },
        "get_typing_capabilities": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }