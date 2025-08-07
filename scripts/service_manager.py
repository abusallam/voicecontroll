#!/usr/bin/env python3
"""
Voxtral Service Manager
Prevents duplicate instances and manages service lifecycle
"""

import os
import sys
import psutil
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config

@dataclass
class ProcessInfo:
    """Information about a running process"""
    pid: int
    name: str
    cmdline: List[str]
    port: Optional[int]
    start_time: float

class ServiceManager:
    """Manages Voxtral service instances and prevents duplicates"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = project_root
        self.lock_file = Path.home() / ".local/share/voxtral/voxtral.lock"
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        
    def check_existing_instances(self) -> List[ProcessInfo]:
        """Find all existing Voxtral processes"""
        instances = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    proc_info = proc.info
                    if not proc_info or not proc_info.get('cmdline'):
                        continue
                    
                    cmdline = proc_info['cmdline']
                    cmdline_str = ' '.join(cmdline) if cmdline else ''
                    
                    # Check if this is a Voxtral process
                    if self._is_voxtral_process(cmdline_str, proc_info['name']):
                        instances.append(ProcessInfo(
                            pid=proc_info['pid'],
                            name=proc_info['name'],
                            cmdline=cmdline,
                            port=None,  # We'll detect port later if needed
                            start_time=proc_info['create_time']
                        ))
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error checking existing instances: {e}")
            
        return instances
    
    def _is_voxtral_process(self, cmdline: str, process_name: str) -> bool:
        """Check if a process is a Voxtral process"""
        voxtral_indicators = [
            'voxtral_tray_gtk.py',
            'voxtral_tray_unified.py',
            'tray_icon.py',
            'agent_main.py',
            'voxtral-tray',
            'VoxtralTrayGTK',
            'VoxtralTrayApp',
            'VoxtralTrayUnified'
        ]
        
        cmdline_lower = cmdline.lower()
        name_lower = process_name.lower() if process_name else ''
        
        for indicator in voxtral_indicators:
            if indicator.lower() in cmdline_lower or indicator.lower() in name_lower:
                return True
                
        return False
    
    def terminate_duplicates(self, keep_newest: bool = True) -> bool:
        """Terminate duplicate instances, keeping the newest or oldest"""
        instances = self.check_existing_instances()
        
        if len(instances) <= 1:
            self.logger.info("No duplicate instances found")
            return True
            
        self.logger.warning(f"Found {len(instances)} Voxtral instances, terminating duplicates")
        
        # Sort by start time
        instances.sort(key=lambda x: x.start_time, reverse=keep_newest)
        
        # Keep the first one (newest or oldest based on keep_newest)
        keep_instance = instances[0]
        terminate_instances = instances[1:]
        
        self.logger.info(f"Keeping instance PID {keep_instance.pid} (started at {keep_instance.start_time})")
        
        success = True
        for instance in terminate_instances:
            try:
                self.logger.info(f"Terminating duplicate instance PID {instance.pid}")
                proc = psutil.Process(instance.pid)
                
                # Try graceful termination first
                proc.terminate()
                
                # Wait for graceful shutdown
                try:
                    proc.wait(timeout=5)
                    self.logger.info(f"Successfully terminated PID {instance.pid}")
                except psutil.TimeoutExpired:
                    # Force kill if needed
                    self.logger.warning(f"Force killing PID {instance.pid}")
                    proc.kill()
                    proc.wait()
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.error(f"Failed to terminate PID {instance.pid}: {e}")
                success = False
                
        return success
    
    def setup_preferred_autostart(self, method: str = "systemd") -> bool:
        """Setup preferred autostart method and disable others"""
        self.logger.info(f"Setting up preferred autostart method: {method}")
        
        if method == "systemd":
            return self._setup_systemd_autostart()
        elif method == "desktop":
            return self._setup_desktop_autostart()
        elif method == "manual":
            return self._cleanup_all_autostart()
        else:
            self.logger.error(f"Unknown autostart method: {method}")
            return False
    
    def _setup_systemd_autostart(self) -> bool:
        """Setup systemd user service and disable desktop autostart"""
        try:
            # First, cleanup conflicting desktop autostart
            self._cleanup_desktop_autostart()
            
            # Create systemd service
            systemd_dir = Path.home() / ".config/systemd/user"
            systemd_dir.mkdir(parents=True, exist_ok=True)
            
            service_file = systemd_dir / "voxtral-tray.service"
            python_path = self.project_root / ".venv/bin/python"
            script_path = self.project_root / "scripts/voxtral_tray_unified.py"  # We'll create this
            
            service_content = f"""[Unit]
Description=Voxtral Agentic Voice Platform Tray
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Restart=always
RestartSec=5
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=%i
ExecStartPre=/bin/sleep 10
ExecStart={python_path} {script_path}
WorkingDirectory={self.project_root}

[Install]
WantedBy=default.target
"""
            
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Reload systemd and enable service
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', '--user', 'enable', 'voxtral-tray.service'], check=True)
            
            self.logger.info("Systemd autostart configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup systemd autostart: {e}")
            return False
    
    def _setup_desktop_autostart(self) -> bool:
        """Setup desktop autostart and disable systemd service"""
        try:
            # First, cleanup conflicting systemd service
            self._cleanup_systemd_autostart()
            
            # Create desktop autostart
            autostart_dir = Path.home() / ".config/autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / "voxtral-tray.desktop"
            python_path = self.project_root / ".venv/bin/python"
            script_path = self.project_root / "scripts/voxtral_tray_unified.py"  # We'll create this
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=Voxtral Voice Agent
Comment=AI-powered voice assistant for Linux
Exec={python_path} {script_path}
Icon={self.project_root}/scripts/icon.png
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Utility;AudioVideo;
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            self.logger.info("Desktop autostart configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup desktop autostart: {e}")
            return False
    
    def cleanup_conflicting_autostart(self) -> bool:
        """Remove all autostart configurations"""
        return self._cleanup_all_autostart()
    
    def _cleanup_systemd_autostart(self) -> bool:
        """Remove systemd autostart configuration"""
        try:
            # Stop and disable service
            subprocess.run(['systemctl', '--user', 'stop', 'voxtral-tray.service'], 
                         capture_output=True)
            subprocess.run(['systemctl', '--user', 'disable', 'voxtral-tray.service'], 
                         capture_output=True)
            
            # Remove service file
            service_file = Path.home() / ".config/systemd/user/voxtral-tray.service"
            if service_file.exists():
                service_file.unlink()
                
            # Reload systemd
            subprocess.run(['systemctl', '--user', 'daemon-reload'], 
                         capture_output=True)
            
            self.logger.info("Systemd autostart cleaned up")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup systemd autostart: {e}")
            return False
    
    def _cleanup_desktop_autostart(self) -> bool:
        """Remove desktop autostart configuration"""
        try:
            desktop_file = Path.home() / ".config/autostart/voxtral-tray.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
                self.logger.info("Desktop autostart cleaned up")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup desktop autostart: {e}")
            return False
    
    def _cleanup_all_autostart(self) -> bool:
        """Remove all autostart configurations"""
        systemd_success = self._cleanup_systemd_autostart()
        desktop_success = self._cleanup_desktop_autostart()
        return systemd_success and desktop_success
    
    def create_lock_file(self) -> bool:
        """Create lock file to prevent multiple instances"""
        try:
            if self.lock_file.exists():
                # Check if the PID in lock file is still running
                try:
                    with open(self.lock_file, 'r') as f:
                        old_pid = int(f.read().strip())
                    
                    if psutil.pid_exists(old_pid):
                        proc = psutil.Process(old_pid)
                        if self._is_voxtral_process(' '.join(proc.cmdline()), proc.name()):
                            self.logger.warning(f"Lock file exists with running PID {old_pid}")
                            return False
                    
                    # Old PID is dead, remove stale lock file
                    self.lock_file.unlink()
                    
                except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
                    # Invalid or dead PID, remove lock file
                    self.lock_file.unlink()
            
            # Create new lock file
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            self.logger.info(f"Created lock file with PID {os.getpid()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create lock file: {e}")
            return False
    
    def remove_lock_file(self) -> bool:
        """Remove lock file on shutdown"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                self.logger.info("Removed lock file")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove lock file: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        instances = self.check_existing_instances()
        
        # Check systemd service status
        systemd_status = "unknown"
        try:
            result = subprocess.run(['systemctl', '--user', 'is-active', 'voxtral-tray.service'],
                                  capture_output=True, text=True)
            systemd_status = result.stdout.strip()
        except:
            pass
        
        # Check desktop autostart
        desktop_autostart = (Path.home() / ".config/autostart/voxtral-tray.desktop").exists()
        
        # Check lock file
        lock_file_exists = self.lock_file.exists()
        lock_file_pid = None
        if lock_file_exists:
            try:
                with open(self.lock_file, 'r') as f:
                    lock_file_pid = int(f.read().strip())
            except:
                pass
        
        return {
            "running_instances": len(instances),
            "instances": [
                {
                    "pid": inst.pid,
                    "name": inst.name,
                    "cmdline": ' '.join(inst.cmdline),
                    "start_time": inst.start_time
                }
                for inst in instances
            ],
            "systemd_status": systemd_status,
            "desktop_autostart": desktop_autostart,
            "lock_file_exists": lock_file_exists,
            "lock_file_pid": lock_file_pid
        }

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Voxtral Service Manager")
    parser.add_argument("--check", action="store_true", help="Check for existing instances")
    parser.add_argument("--terminate-duplicates", action="store_true", help="Terminate duplicate instances")
    parser.add_argument("--setup-autostart", choices=["systemd", "desktop", "manual"], 
                       help="Setup preferred autostart method")
    parser.add_argument("--cleanup-autostart", action="store_true", help="Remove all autostart configurations")
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = ServiceManager()
    
    if args.check:
        instances = manager.check_existing_instances()
        print(f"Found {len(instances)} Voxtral instances:")
        for inst in instances:
            print(f"  PID {inst.pid}: {inst.name} - {' '.join(inst.cmdline)}")
    
    elif args.terminate_duplicates:
        success = manager.terminate_duplicates()
        print("Duplicate termination:", "SUCCESS" if success else "FAILED")
    
    elif args.setup_autostart:
        success = manager.setup_preferred_autostart(args.setup_autostart)
        print(f"Autostart setup ({args.setup_autostart}):", "SUCCESS" if success else "FAILED")
    
    elif args.cleanup_autostart:
        success = manager.cleanup_conflicting_autostart()
        print("Autostart cleanup:", "SUCCESS" if success else "FAILED")
    
    elif args.status:
        status = manager.get_service_status()
        print("=== Voxtral Service Status ===")
        print(f"Running instances: {status['running_instances']}")
        print(f"Systemd service: {status['systemd_status']}")
        print(f"Desktop autostart: {status['desktop_autostart']}")
        print(f"Lock file: {status['lock_file_exists']} (PID: {status['lock_file_pid']})")
        
        if status['instances']:
            print("\nRunning processes:")
            for inst in status['instances']:
                print(f"  PID {inst['pid']}: {inst['name']}")
                print(f"    Command: {inst['cmdline']}")
                print(f"    Started: {time.ctime(inst['start_time'])}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()