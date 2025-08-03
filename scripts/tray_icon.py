#!/usr/bin/env python3
"""
Voxtral Agentic Platform System Tray
Provides control interface for the voice agent
"""

import os
import sys
import subprocess
import signal
import time
import psutil
from pathlib import Path
from PyQt5 import QtWidgets, QtGui, QtCore

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config

class VoxtralTrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, parent=None):
        # Create icon (use a simple colored circle if icon.png doesn't exist)
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            icon = QtGui.QIcon(str(icon_path))
        else:
            # Create a simple icon programmatically
            pixmap = QtGui.QPixmap(32, 32)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
            painter.drawEllipse(4, 4, 24, 24)
            painter.end()
            icon = QtGui.QIcon(pixmap)
        
        super(VoxtralTrayApp, self).__init__(icon, parent)
        
        self.agent_process = None
        self.vllm_process = None
        self.setToolTip("Voxtral Agentic Voice Platform")
        
        # Setup menu
        self.setup_menu()
        
        # Setup timer to check agent status
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # Check every 2 seconds
        
        # Show startup message
        self.showMessage("Voxtral", "Voice agent tray started", QtWidgets.QSystemTrayIcon.Information, 3000)
    
    def setup_menu(self):
        """Setup the context menu"""
        menu = QtWidgets.QMenu()
        
        # Agent control
        self.start_agent_action = menu.addAction("🎙️ Start Agent")
        self.stop_agent_action = menu.addAction("⏹️ Stop Agent")
        self.restart_agent_action = menu.addAction("🔄 Restart Agent")
        
        menu.addSeparator()
        
        # VLLM server control
        self.start_vllm_action = menu.addAction("🧠 Start VLLM Server")
        self.stop_vllm_action = menu.addAction("⏹️ Stop VLLM Server")
        
        menu.addSeparator()
        
        # Folder access
        open_agent_folder = menu.addAction("📁 Open Agent Folder")
        open_tools_folder = menu.addAction("🔧 Open Tools Folder")
        open_langraph_folder = menu.addAction("🌐 Open LangGraph Folder")
        open_logs = menu.addAction("📋 Open Logs")
        
        menu.addSeparator()
        
        # Configuration
        open_config = menu.addAction("⚙️ Open Configuration")
        
        menu.addSeparator()
        
        # Status and quit
        self.status_action = menu.addAction("📊 Status: Initializing...")
        quit_action = menu.addAction("❌ Quit")
        
        # Connect actions
        self.start_agent_action.triggered.connect(self.start_agent)
        self.stop_agent_action.triggered.connect(self.stop_agent)
        self.restart_agent_action.triggered.connect(self.restart_agent)
        
        self.start_vllm_action.triggered.connect(self.start_vllm_server)
        self.stop_vllm_action.triggered.connect(self.stop_vllm_server)
        
        open_agent_folder.triggered.connect(lambda: self.open_folder("agent"))
        open_tools_folder.triggered.connect(lambda: self.open_folder("tools"))
        open_langraph_folder.triggered.connect(lambda: self.open_folder("langraph"))
        open_logs.triggered.connect(self.open_logs)
        
        open_config.triggered.connect(self.open_config)
        
        quit_action.triggered.connect(self.quit_application)
        
        self.setContextMenu(menu)
    
    def start_agent(self):
        """Start the Voxtral agent"""
        if self.agent_process and self.agent_process.poll() is None:
            self.showMessage("Voxtral", "Agent is already running", QtWidgets.QSystemTrayIcon.Warning, 3000)
            return
        
        try:
            agent_script = project_root / "agent" / "agent_main.py"
            self.agent_process = subprocess.Popen([
                sys.executable, str(agent_script)
            ], cwd=str(project_root))
            
            self.showMessage("Voxtral", "Agent started successfully", QtWidgets.QSystemTrayIcon.Information, 3000)
            
        except Exception as e:
            self.showMessage("Voxtral", f"Failed to start agent: {e}", QtWidgets.QSystemTrayIcon.Critical, 5000)
    
    def stop_agent(self):
        """Stop the Voxtral agent"""
        if not self.agent_process or self.agent_process.poll() is not None:
            self.showMessage("Voxtral", "Agent is not running", QtWidgets.QSystemTrayIcon.Warning, 3000)
            return
        
        try:
            # Send SIGTERM for graceful shutdown
            self.agent_process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.agent_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self.agent_process.kill()
                self.agent_process.wait()
            
            self.agent_process = None
            self.showMessage("Voxtral", "Agent stopped", QtWidgets.QSystemTrayIcon.Information, 3000)
            
        except Exception as e:
            self.showMessage("Voxtral", f"Error stopping agent: {e}", QtWidgets.QSystemTrayIcon.Critical, 5000)
    
    def restart_agent(self):
        """Restart the Voxtral agent"""
        self.stop_agent()
        time.sleep(1)  # Brief pause
        self.start_agent()
    
    def start_vllm_server(self):
        """Start the VLLM server"""
        if self.is_vllm_running():
            self.showMessage("Voxtral", "VLLM server is already running", QtWidgets.QSystemTrayIcon.Warning, 3000)
            return
        
        try:
            model_name = config.get("model_name", "mistralai/Voxtral-Mini-3B-2507")
            
            cmd = [
                "vllm", "serve", model_name,
                "--tokenizer_mode", "mistral",
                "--config_format", "mistral", 
                "--load_format", "mistral"
            ]
            
            self.vllm_process = subprocess.Popen(cmd)
            self.showMessage("Voxtral", "VLLM server starting...", QtWidgets.QSystemTrayIcon.Information, 3000)
            
        except Exception as e:
            self.showMessage("Voxtral", f"Failed to start VLLM server: {e}", QtWidgets.QSystemTrayIcon.Critical, 5000)
    
    def stop_vllm_server(self):
        """Stop the VLLM server"""
        try:
            # Find and kill VLLM processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'vllm' in proc.info['name'].lower() or any('vllm' in arg for arg in proc.info['cmdline']):
                        proc.terminate()
                        proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
            
            self.vllm_process = None
            self.showMessage("Voxtral", "VLLM server stopped", QtWidgets.QSystemTrayIcon.Information, 3000)
            
        except Exception as e:
            self.showMessage("Voxtral", f"Error stopping VLLM server: {e}", QtWidgets.QSystemTrayIcon.Critical, 5000)
    
    def is_vllm_running(self) -> bool:
        """Check if VLLM server is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if not proc_info or not proc_info.get('name') or not proc_info.get('cmdline'):
                        continue
                    
                    name = proc_info['name'].lower()
                    cmdline = proc_info.get('cmdline', [])
                    
                    if 'vllm' in name or any('vllm' in str(arg) for arg in cmdline if arg):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError, TypeError):
                    continue
            return False
        except Exception as e:
            print(f"Error checking VLLM status: {e}")
            return False
    
    def update_status(self):
        """Update the status display"""
        try:
            # Safely check agent status
            agent_running = False
            if self.agent_process:
                poll_result = self.agent_process.poll()
                agent_running = poll_result is None
            
            # Safely check VLLM status
            vllm_running = self.is_vllm_running()
            if vllm_running is None:
                vllm_running = False
            
            # Update status text
            if agent_running and vllm_running:
                status = "📊 Status: Running (Agent + VLLM)"
                self.setToolTip("Voxtral: Agent and VLLM running")
            elif agent_running:
                status = "📊 Status: Agent running (VLLM stopped)"
                self.setToolTip("Voxtral: Agent running, VLLM stopped")
            elif vllm_running:
                status = "📊 Status: VLLM running (Agent stopped)"
                self.setToolTip("Voxtral: VLLM running, Agent stopped")
            else:
                status = "📊 Status: Stopped"
                self.setToolTip("Voxtral: All services stopped")
            
            if hasattr(self, 'status_action') and self.status_action:
                self.status_action.setText(status)
            
            # Update menu item states safely with explicit boolean conversion
            if hasattr(self, 'start_agent_action') and self.start_agent_action:
                self.start_agent_action.setEnabled(bool(not agent_running))
            if hasattr(self, 'stop_agent_action') and self.stop_agent_action:
                self.stop_agent_action.setEnabled(bool(agent_running))
            if hasattr(self, 'restart_agent_action') and self.restart_agent_action:
                self.restart_agent_action.setEnabled(bool(agent_running))
            
            if hasattr(self, 'start_vllm_action') and self.start_vllm_action:
                self.start_vllm_action.setEnabled(bool(not vllm_running))
            if hasattr(self, 'stop_vllm_action') and self.stop_vllm_action:
                self.stop_vllm_action.setEnabled(bool(vllm_running))
                
        except Exception as e:
            print(f"Error updating status: {e}")
            import traceback
            traceback.print_exc()
    
    def open_folder(self, folder_name):
        """Open a project folder"""
        folder_path = project_root / folder_name
        if folder_path.exists():
            subprocess.Popen(["xdg-open", str(folder_path)])
        else:
            self.showMessage("Voxtral", f"Folder not found: {folder_name}", QtWidgets.QSystemTrayIcon.Warning, 3000)
    
    def open_logs(self):
        """Open the log file"""
        log_file = project_root / "voxtral.log"
        if log_file.exists():
            subprocess.Popen(["xdg-open", str(log_file)])
        else:
            self.showMessage("Voxtral", "No log file found", QtWidgets.QSystemTrayIcon.Warning, 3000)
    
    def open_config(self):
        """Open the configuration file"""
        config_file = project_root / "config" / "voxtral.yaml"
        subprocess.Popen(["xdg-open", str(config_file)])
    
    def quit_application(self):
        """Quit the application"""
        # Stop all processes
        self.stop_agent()
        self.stop_vllm_server()
        
        QtWidgets.qApp.quit()

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Check if system tray is available
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(None, "Voxtral Tray",
                                     "System tray is not available on this system.")
        sys.exit(1)
    
    # Prevent application from quitting when last window is closed
    app.setQuitOnLastWindowClosed(False)
    
    tray_icon = VoxtralTrayApp()
    tray_icon.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
