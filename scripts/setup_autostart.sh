#!/bin/bash
set -e

echo "🚀 Setting up Voxtral Auto-Startup"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get the absolute path to the project
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$PROJECT_ROOT/.venv/bin/python"
SCRIPT_PATH="$PROJECT_ROOT/scripts/voxtral_tray_gtk.py"

print_status "Project root: $PROJECT_ROOT"
print_status "Python path: $PYTHON_PATH"
print_status "Script path: $SCRIPT_PATH"

# Create systemd user service directory
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

# Create the systemd service file
SERVICE_FILE="$SYSTEMD_USER_DIR/voxtral-tray.service"

print_status "Creating systemd service file: $SERVICE_FILE"

cat > "$SERVICE_FILE" << EOF
[Unit]
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
ExecStart=$PYTHON_PATH $SCRIPT_PATH
WorkingDirectory=$PROJECT_ROOT

# Ensure the service starts after the desktop environment is ready
ExecStartPre=/bin/sleep 10

[Install]
WantedBy=default.target
EOF

print_success "Systemd service file created"

# Create desktop autostart entry (alternative method)
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

DESKTOP_FILE="$AUTOSTART_DIR/voxtral-tray.desktop"

print_status "Creating desktop autostart file: $DESKTOP_FILE"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Voxtral Voice Agent
Comment=AI-powered voice assistant for Linux
Exec=$PYTHON_PATH $SCRIPT_PATH
Icon=$PROJECT_ROOT/scripts/icon.png
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Utility;AudioVideo;
EOF

print_success "Desktop autostart file created"

# Enable and start the systemd service
print_status "Enabling systemd user service..."
systemctl --user daemon-reload
systemctl --user enable voxtral-tray.service

print_success "Auto-startup configured successfully!"
echo
echo "📋 Auto-startup methods configured:"
echo "1. Systemd user service: voxtral-tray.service"
echo "2. Desktop autostart entry: ~/.config/autostart/voxtral-tray.desktop"
echo
echo "🔧 To manage the service:"
echo "  Start:   systemctl --user start voxtral-tray.service"
echo "  Stop:    systemctl --user stop voxtral-tray.service"
echo "  Status:  systemctl --user status voxtral-tray.service"
echo "  Disable: systemctl --user disable voxtral-tray.service"
echo
echo "🎯 The tray icon will appear automatically after next login/restart!"

# Ask if user wants to start the service now
read -p "Start the service now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting voxtral-tray service..."
    systemctl --user start voxtral-tray.service
    print_success "Service started! Check your system tray."
else
    print_warning "Service will start automatically on next login"
fi