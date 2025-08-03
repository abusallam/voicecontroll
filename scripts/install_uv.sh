#!/bin/bash
set -e

echo "🧠 Voxtral Agentic Voice Platform - UV Installation Script"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    print_error "UV package manager not found!"
    print_status "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    
    if ! command -v uv &> /dev/null; then
        print_error "Failed to install UV. Please install manually: https://docs.astral.sh/uv/"
        exit 1
    fi
fi

print_success "UV package manager found: $(uv --version)"

# Check if running on supported system
print_status "Checking system compatibility..."

if [[ ! -f /etc/debian_version ]]; then
    print_warning "This script is optimized for Debian-based systems"
    print_warning "You may need to adapt package names for your distribution"
fi

# Check for Wayland
if [[ -n "$WAYLAND_DISPLAY" ]]; then
    print_success "Wayland display server detected"
    DISPLAY_SERVER="wayland"
elif [[ -n "$DISPLAY" ]]; then
    print_success "X11 display server detected"
    DISPLAY_SERVER="x11"
else
    print_warning "No display server detected - some features may not work"
    DISPLAY_SERVER="none"
fi

# Update package lists
print_status "Updating package lists..."
sudo apt update

# Install system dependencies
print_status "Installing system dependencies..."

SYSTEM_PACKAGES=(
    "python3"
    "python3-pip" 
    "python3-venv"
    "python3-dev"
    "ffmpeg"
    "xdg-utils"
    "portaudio19-dev"
    "libsndfile1-dev"
    "libasound2-dev"
    "pulseaudio"
    "pulseaudio-utils"
    "libayatana-appindicator3-1"
    "gir1.2-ayatanaappindicator3-0.1"
    "python3-gi"
    "python3-gi-cairo"
    "libgirepository1.0-dev"
    "libcairo2-dev"
    "pkg-config"
    "ydotool"  # Better Wayland typing support
)

# Add Wayland-specific packages
if [[ "$DISPLAY_SERVER" == "wayland" ]]; then
    SYSTEM_PACKAGES+=("wtype" "wl-clipboard")
    print_status "Adding Wayland-specific packages: wtype, wl-clipboard"
fi

# Add X11-specific packages  
if [[ "$DISPLAY_SERVER" == "x11" ]]; then
    SYSTEM_PACKAGES+=("xdotool" "xclip")
    print_status "Adding X11-specific packages: xdotool, xclip"
fi

# Install packages
for package in "${SYSTEM_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $package "; then
        print_success "$package already installed"
    else
        print_status "Installing $package..."
        sudo apt install -y "$package"
    fi
done

# Check for GPU support
print_status "Checking GPU support..."
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU detected"
    GPU_SUPPORT="nvidia"
elif lspci | grep -i amd | grep -i vga &> /dev/null; then
    print_success "AMD GPU detected"
    GPU_SUPPORT="amd"
else
    print_warning "No dedicated GPU detected - using CPU inference"
    GPU_SUPPORT="cpu"
fi

# Create UV project and install dependencies
print_status "Creating UV project and installing dependencies..."

# Initialize UV project if not already done
if [[ ! -f ".python-version" ]]; then
    uv python install 3.11
    uv python pin 3.11
fi

# Install dependencies based on GPU support
if [[ "$GPU_SUPPORT" == "nvidia" ]]; then
    print_status "Installing dependencies with CUDA support..."
    uv sync --extra gpu
elif [[ "$GPU_SUPPORT" == "amd" ]]; then
    print_status "Installing dependencies with ROCm support..."
    # For now, use CPU version as ROCm support varies
    uv sync --extra cpu
else
    print_status "Installing CPU-only dependencies..."
    uv sync --extra cpu
fi

# Install development dependencies if requested
read -p "Install development dependencies? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Installing development dependencies..."
    uv sync --extra dev
fi

# Setup audio permissions
print_status "Setting up audio permissions..."
sudo usermod -a -G audio $USER

# Configure PulseAudio for low latency
print_status "Configuring PulseAudio for low latency..."
PULSE_CONFIG="$HOME/.config/pulse/daemon.conf"
mkdir -p "$(dirname "$PULSE_CONFIG")"

if [[ ! -f "$PULSE_CONFIG" ]]; then
    cat > "$PULSE_CONFIG" << EOF
# Voxtral optimized PulseAudio configuration
default-sample-format = s16le
default-sample-rate = 16000
alternate-sample-rate = 48000
default-sample-channels = 1
default-fragments = 2
default-fragment-size-msec = 25
EOF
    print_success "PulseAudio configuration created"
else
    print_success "PulseAudio configuration already exists"
fi

# Setup ydotool service for better Wayland support
if [[ "$DISPLAY_SERVER" == "wayland" ]]; then
    print_status "Setting up ydotool for Wayland typing support..."
    
    # Create ydotool service
    sudo tee /etc/systemd/system/ydotool.service > /dev/null << EOF
[Unit]
Description=ydotool daemon
After=display-manager.service

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/ydotoold
User=root
Group=input

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start ydotool service
    sudo systemctl daemon-reload
    sudo systemctl enable ydotool.service
    sudo systemctl start ydotool.service
    
    # Add user to input group for ydotool access
    sudo usermod -a -G input $USER
    
    print_success "ydotool service configured"
fi

# Create desktop entry
print_status "Creating desktop entry..."
DESKTOP_FILE="$HOME/.local/share/applications/voxtral.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Voxtral Voice Agent
Comment=AI-powered voice assistant for Linux
Exec=$(pwd)/.venv/bin/python $(pwd)/scripts/voxtral_tray_gtk.py
Icon=$(pwd)/scripts/icon.png
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
StartupNotify=true
EOF

print_success "Desktop entry created"

# Create simple icon if it doesn't exist
ICON_FILE="scripts/icon.png"
if [[ ! -f "$ICON_FILE" ]]; then
    print_status "Creating default icon..."
    # Create a simple PNG icon using ImageMagick if available
    if command -v convert &> /dev/null; then
        convert -size 64x64 xc:transparent -fill blue -draw "circle 32,32 32,16" "$ICON_FILE"
        print_success "Default icon created"
    else
        print_warning "ImageMagick not found - icon will be generated programmatically"
    fi
fi

# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

print_success "Installation completed successfully!"
echo
echo "🎉 Voxtral Agentic Voice Platform is ready!"
echo "============================================"
echo
echo "📋 Next steps:"
echo "1. Start the system:"
echo "   uv run scripts/start_voxtral.sh tray"
echo
echo "2. Or run tests:"
echo "   uv run scripts/test_system.py"
echo
echo "3. Or start components individually:"
echo "   uv run scripts/voxtral_tray_gtk.py"
echo
echo "📁 Configuration file: config/voxtral.yaml"
echo "📋 Logs will be written to: voxtral.log"
echo

if [[ "$DISPLAY_SERVER" == "wayland" ]]; then
    print_warning "⚠️  For Wayland typing support, you may need to log out and back in"
    print_warning "⚠️  This ensures ydotool service and group membership take effect"
fi

if groups | grep -q audio && groups | grep -q input; then
    print_success "Audio and input group membership confirmed"
else
    print_warning "⚠️  You may need to log out and back in for group changes to take effect"
fi

echo
print_success "Happy voice commanding with UV! 🎙️"