#!/usr/bin/env python3
"""
Safe Shell Tool for Voxtral Agent
Executes shell commands with safety restrictions
"""

import subprocess
import logging
import os
import shlex
from typing import Dict, Any
from langchain.tools import tool

logger = logging.getLogger(__name__)

# Dangerous commands to block
BLOCKED_COMMANDS = {
    'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs', 'dd',
    'sudo', 'su', 'passwd', 'chmod', 'chown', 'mount', 'umount',
    'systemctl', 'service', 'init', 'shutdown', 'reboot', 'halt',
    'iptables', 'ufw', 'firewall-cmd', 'kill', 'killall', 'pkill'
}

# Safe commands that are allowed
SAFE_COMMANDS = {
    'ls', 'dir', 'pwd', 'cd', 'cat', 'less', 'more', 'head', 'tail',
    'grep', 'find', 'locate', 'which', 'whereis', 'file', 'stat',
    'ps', 'top', 'htop', 'df', 'du', 'free', 'uptime', 'whoami',
    'date', 'cal', 'echo', 'printf', 'wc', 'sort', 'uniq', 'cut',
    'awk', 'sed', 'tr', 'tee', 'xargs', 'history', 'alias',
    'git', 'python3', 'pip3', 'node', 'npm', 'curl', 'wget',
    'ping', 'traceroute', 'nslookup', 'dig', 'netstat', 'ss'
}

@tool
def run_shell(command: str) -> str:
    """
    Execute a safe shell command on Linux.
    
    Args:
        command: The shell command to execute
        
    Returns:
        Command output or error message
    """
    try:
        # Parse command to check safety
        args = shlex.split(command)
        if not args:
            return "Error: Empty command"
        
        base_command = args[0].split('/')[-1]  # Handle full paths
        
        # Check if command is blocked
        if base_command in BLOCKED_COMMANDS:
            return f"Error: Command '{base_command}' is not allowed for security reasons"
        
        # Warn about potentially unsafe commands
        if base_command not in SAFE_COMMANDS:
            logger.warning(f"Executing potentially unsafe command: {base_command}")
        
        # Set safe environment
        safe_env = os.environ.copy()
        safe_env['PATH'] = '/usr/local/bin:/usr/bin:/bin'
        
        # Execute command with timeout
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            env=safe_env,
            cwd=os.path.expanduser('~')  # Run in user home directory
        )
        
        # Combine stdout and stderr
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        
        if result.returncode != 0:
            output += f"\nExit code: {result.returncode}"
        
        # Limit output length
        if len(output) > 2000:
            output = output[:2000] + "\n... (output truncated)"
        
        return output or "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except subprocess.CalledProcessError as e:
        return f"Error: Command failed with exit code {e.returncode}: {e.stderr}"
    except Exception as e:
        logger.error(f"Shell command execution error: {e}")
        return f"Error: {str(e)}"

def get_shell_tool_schema() -> Dict[str, Any]:
    """Get the schema for the shell tool"""
    return {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute (safe commands only)"
            }
        },
        "required": ["command"]
    }