#!/bin/bash
set -e

echo "🚀 Voxtral Advanced Agentic Voice Platform - Debian 13 Installation"
echo "=================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_feature() {
    echo -e "${PURPLE}[FEATURE]${NC} $1"
}

# Check if running on Debian 13
print_status "Checking Debian 13 compatibility..."
if [[ -f /etc/debian_version ]]; then
    DEBIAN_VERSION=$(cat /etc/debian_version)
    print_success "Debian version detected: $DEBIAN_VERSION"
    
    # Check for Debian 13 (Trixie)
    if [[ "$DEBIAN_VERSION" == *"13"* ]] || [[ "$DEBIAN_VERSION" == *"trixie"* ]]; then
        print_success "✅ Debian 13 (Trixie) confirmed - optimal compatibility"
    else
        print_warning "⚠️ Not Debian 13 - some features may need adaptation"
    fi
else
    print_error "❌ Not a Debian-based system - installation may fail"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for required system features
print_status "Checking system capabilities..."

# Check display server
if [[ -n "$WAYLAND_DISPLAY" ]]; then
    print_success "✅ Wayland display server detected (optimal for Debian 13)"
    DISPLAY_SERVER="wayland"
elif [[ -n "$DISPLAY" ]]; then
    print_success "✅ X11 display server detected (fallback mode)"
    DISPLAY_SERVER="x11"
else
    print_warning "⚠️ No display server detected"
    DISPLAY_SERVER="none"
fi

# Check audio system
if command -v pipewire &> /dev/null; then
    print_success "✅ PipeWire detected (Debian 13 default)"
    AUDIO_SYSTEM="pipewire"
elif command -v pulseaudio &> /dev/null; then
    print_success "✅ PulseAudio detected (fallback)"
    AUDIO_SYSTEM="pulseaudio"
else
    print_warning "⚠️ No audio system detected"
    AUDIO_SYSTEM="none"
fi

# Check UV package manager
if ! command -v uv &> /dev/null; then
    print_error "❌ UV package manager not found!"
    print_status "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    
    if ! command -v uv &> /dev/null; then
        print_error "Failed to install UV. Please install manually: https://docs.astral.sh/uv/"
        exit 1
    fi
fi

print_success "✅ UV package manager found: $(uv --version)"

# Update package lists
print_status "Updating package lists..."
sudo apt update

# Install Debian 13 optimized system dependencies
print_status "Installing Debian 13 optimized system dependencies..."

DEBIAN13_PACKAGES=(
    # Core Python and development
    "python3"
    "python3-pip"
    "python3-venv"
    "python3-dev"
    "python3-full"
    
    # Audio processing (PipeWire optimized)
    "pipewire"
    "pipewire-pulse"
    "pipewire-alsa"
    "wireplumber"
    "libpipewire-0.3-dev"
    "portaudio19-dev"
    "libsndfile1-dev"
    "libasound2-dev"
    
    # GTK and UI (latest versions)
    "libayatana-appindicator3-1"
    "gir1.2-ayatanaappindicator3-0.1"
    "python3-gi"
    "python3-gi-cairo"
    "libgirepository1.0-dev"
    "libcairo2-dev"
    "libgtk-3-dev"
    "libgtk-4-dev"
    
    # Wayland tools (Debian 13 optimized)
    "wtype"
    "wl-clipboard"
    "wayland-protocols"
    "libwayland-dev"
    
    # Input simulation
    "ydotool"
    "libevdev-dev"
    "libudev-dev"
    
    # X11 fallback
    "xdotool"
    "xclip"
    "x11-utils"
    
    # System utilities
    "ffmpeg"
    "xdg-utils"
    "pkg-config"
    "build-essential"
    "cmake"
    "git"
    
    # Security and permissions
    "policykit-1"
    "libpolkit-gobject-1-dev"
    
    # Performance monitoring
    "htop"
    "iotop"
    "nethogs"
    
    # Development tools
    "curl"
    "wget"
    "unzip"
    "software-properties-common"
)

# Install packages with progress
for package in "${DEBIAN13_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $package "; then
        print_success "✅ $package already installed"
    else
        print_status "📦 Installing $package..."
        sudo apt install -y "$package" || print_warning "⚠️ Failed to install $package"
    fi
done

# Check for GPU support
print_status "Checking GPU acceleration support..."
if command -v nvidia-smi &> /dev/null; then
    print_success "✅ NVIDIA GPU detected"
    GPU_SUPPORT="nvidia"
    
    # Install NVIDIA CUDA support for Debian 13
    print_status "Installing NVIDIA CUDA support..."
    sudo apt install -y nvidia-cuda-toolkit nvidia-cuda-dev || print_warning "⚠️ CUDA installation failed"
    
elif lspci | grep -i amd | grep -i vga &> /dev/null; then
    print_success "✅ AMD GPU detected"
    GPU_SUPPORT="amd"
    
    # Install AMD ROCm support if available
    print_status "Installing AMD ROCm support..."
    sudo apt install -y rocm-dev rocm-libs || print_warning "⚠️ ROCm not available, using CPU"
    
else
    print_warning "⚠️ No dedicated GPU detected - using optimized CPU inference"
    GPU_SUPPORT="cpu"
fi

# Setup UV project with Debian 13 optimizations
print_status "Setting up UV project with Debian 13 optimizations..."

# Initialize UV project if not already done
if [[ ! -f ".python-version" ]]; then
    uv python install 3.11
    uv python pin 3.11
fi

# Install dependencies based on GPU support and Debian 13
if [[ "$GPU_SUPPORT" == "nvidia" ]]; then
    print_feature "🚀 Installing with NVIDIA GPU acceleration..."
    uv sync --extra gpu --extra debian13
elif [[ "$GPU_SUPPORT" == "amd" ]]; then
    print_feature "🚀 Installing with AMD GPU acceleration..."
    uv sync --extra amd --extra debian13
else
    print_feature "🚀 Installing with optimized CPU inference..."
    uv sync --extra cpu --extra debian13
fi

# Install development dependencies
read -p "Install development and debugging tools? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_status "Installing development dependencies..."
    uv sync --extra dev
fi

# Setup advanced audio configuration for Debian 13
print_status "Configuring advanced audio system..."

if [[ "$AUDIO_SYSTEM" == "pipewire" ]]; then
    print_feature "🎵 Configuring PipeWire for optimal voice processing..."
    
    # Create PipeWire configuration directory
    mkdir -p "$HOME/.config/pipewire"
    
    # Create optimized PipeWire configuration
    cat > "$HOME/.config/pipewire/pipewire.conf.d/99-voxtral.conf" << EOF
# Voxtral optimized PipeWire configuration for Debian 13
context.properties = {
    default.clock.rate = 16000
    default.clock.quantum = 256
    default.clock.min-quantum = 64
    default.clock.max-quantum = 2048
}

context.modules = [
    { name = libpipewire-module-rt
        args = {
            nice.level = -11
            rt.prio = 88
            rt.time.soft = 200000
            rt.time.hard = 200000
        }
        flags = [ ifexists nofail ]
    }
]
EOF
    
    # Restart PipeWire services
    systemctl --user restart pipewire pipewire-pulse
    print_success "✅ PipeWire optimized for voice processing"
    
else
    print_feature "🎵 Configuring PulseAudio fallback..."
    
    # Create PulseAudio configuration
    PULSE_CONFIG="$HOME/.config/pulse/daemon.conf"
    mkdir -p "$(dirname "$PULSE_CONFIG")"
    
    cat > "$PULSE_CONFIG" << EOF
# Voxtral optimized PulseAudio configuration
default-sample-format = s16le
default-sample-rate = 16000
alternate-sample-rate = 48000
default-sample-channels = 1
default-fragments = 2
default-fragment-size-msec = 25
high-priority = yes
nice-level = -11
realtime-scheduling = yes
realtime-priority = 5
EOF
    
    systemctl --user restart pulseaudio
    print_success "✅ PulseAudio optimized for voice processing"
fi

# Setup advanced input system for Debian 13
print_status "Configuring advanced input system..."

if [[ "$DISPLAY_SERVER" == "wayland" ]]; then
    print_feature "🖱️ Setting up Wayland input optimization..."
    
    # Setup ydotool service for advanced input
    sudo tee /etc/systemd/system/ydotool.service > /dev/null << EOF
[Unit]
Description=ydotool daemon for advanced input simulation
After=display-manager.service
Wants=display-manager.service

[Service]
Type=simple
Restart=always
RestartSec=1
ExecStart=/usr/bin/ydotoold
User=root
Group=input
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start ydotool service
    sudo systemctl daemon-reload
    sudo systemctl enable ydotool.service
    sudo systemctl start ydotool.service
    
    # Add user to input group
    sudo usermod -a -G input $USER
    
    print_success "✅ Advanced Wayland input system configured"
fi

# Setup user permissions and groups
print_status "Setting up user permissions..."
sudo usermod -a -G audio,input,video $USER

# Create advanced desktop entry
print_status "Creating advanced desktop integration..."
DESKTOP_FILE="$HOME/.local/share/applications/voxtral-advanced.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Voxtral Advanced Agentic Platform
Comment=Advanced AI-powered voice assistant with agentic capabilities
Exec=$(pwd)/.venv/bin/python $(pwd)/scripts/voxtral_agentic_complete.py
Icon=$(pwd)/scripts/icon.png
Terminal=false
Type=Application
Categories=Utility;AudioVideo;Development;
StartupNotify=true
Keywords=voice;ai;agent;transcription;automation;
StartupWMClass=voxtral-advanced
EOF

print_success "✅ Advanced desktop entry created"

# Create systemd user service for auto-start
print_status "Creating systemd user service..."
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_DIR/voxtral-advanced.service" << EOF
[Unit]
Description=Voxtral Advanced Agentic Voice Platform
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Restart=always
RestartSec=3
ExecStart=$(pwd)/.venv/bin/python $(pwd)/scripts/voxtral_agentic_complete.py
WorkingDirectory=$(pwd)
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0

[Install]
WantedBy=default.target
EOF

# Enable the service
systemctl --user daemon-reload
systemctl --user enable voxtral-advanced.service

print_success "✅ Systemd user service created and enabled"

# Create advanced configuration
print_status "Setting up advanced configuration..."
cp config/advanced_voxtral.yaml config/voxtral.yaml
print_success "✅ Advanced configuration activated"

# Make all scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Final system optimization
print_status "Applying final system optimizations..."

# Increase file descriptor limits for better performance
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize kernel parameters for audio processing
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
echo "kernel.sched_rt_runtime_us=950000" | sudo tee -a /etc/sysctl.conf

print_success "✅ System optimizations applied"

# Installation complete
print_success "🎉 Voxtral Advanced Agentic Platform installation completed!"
echo
echo "🚀 DEBIAN 13 OPTIMIZED INSTALLATION COMPLETE!"
echo "=============================================="
echo
print_feature "🎯 Advanced Features Installed:"
echo "   ✅ Enhanced AI voice transcription (Whisper small model)"
echo "   ✅ Global hotkeys (Ctrl+Alt activation)"
echo "   ✅ Agentic workflow processing"
echo "   ✅ Advanced memory management"
echo "   ✅ Performance monitoring"
echo "   ✅ Development tools integration"
echo "   ✅ Debian 13 optimizations"
echo "   ✅ PipeWire/PulseAudio optimization"
echo "   ✅ Wayland/X11 compatibility"
echo "   ✅ Systemd service integration"
echo
echo "📋 Next steps:"
echo "1. Log out and back in (for group permissions)"
echo "2. Start the advanced platform:"
echo "   uv run scripts/voxtral_agentic_complete.py"
echo
echo "3. Or enable auto-start:"
echo "   systemctl --user start voxtral-advanced.service"
echo
echo "4. Test the system:"
echo "   uv run scripts/test_system.py"
echo
echo "🎙️ Global Hotkeys:"
echo "   • Ctrl+Alt: Toggle voice listening"
echo "   • Ctrl+Shift+V: Quick record"
echo "   • Ctrl+Shift+S: Emergency stop"
echo
echo "📁 Configuration: config/voxtral.yaml"
echo "📋 Logs: voxtral.log"
echo

if [[ "$DISPLAY_SERVER" == "wayland" ]]; then
    print_warning "⚠️ IMPORTANT: Log out and back in for Wayland permissions to take effect"
fi

if [[ "$AUDIO_SYSTEM" == "pipewire" ]]; then
    print_success "🎵 PipeWire optimized for Debian 13 - optimal performance expected"
fi

echo
print_success "🎉 Ready for advanced agentic voice interactions on Debian 13! 🎙️🤖"