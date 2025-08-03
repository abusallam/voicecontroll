#!/bin/bash
set -e

echo "🧠 Voxtral Agentic Voice Platform - Installation Script"
echo "======================================================"

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

# Create virtual environment
print_status "Creating Python virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."

# Install PyTorch with appropriate GPU support
if [[ "$GPU_SUPPORT" == "nvidia" ]]; then
    print_status "Installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
elif [[ "$GPU_SUPPORT" == "amd" ]]; then
    print_status "Installing PyTorch with ROCm support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6
else
    print_status "Installing PyTorch CPU version..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install other requirements
print_status "Installing other Python packages..."
pip install -r requirements.txt

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

# Create desktop entry
print_status "Creating desktop entry..."
DESKTOP_FILE="$HOME/.local/share/applications/voxtral.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Voxtral Voice Agent
Comment=AI-powered voice assistant for Linux
Exec=$(pwd)/venv/bin/python $(pwd)/scripts/tray_icon.py
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

# Service restart recommendations
print_status "Checking services that may need restart..."

SERVICES_TO_RESTART=()

# Check PulseAudio
if systemctl --user is-active --quiet pulseaudio; then
    SERVICES_TO_RESTART+=("pulseaudio")
fi

# Check PipeWire (alternative to PulseAudio)
if systemctl --user is-active --quiet pipewire; then
    SERVICES_TO_RESTART+=("pipewire")
fi

if [[ ${#SERVICES_TO_RESTART[@]} -gt 0 ]]; then
    print_warning "The following services should be restarted for optimal performance:"
    for service in "${SERVICES_TO_RESTART[@]}"; do
        echo "  - $service"
    done
    
    read -p "Restart these services now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for service in "${SERVICES_TO_RESTART[@]}"; do
            print_status "Restarting $service..."
            systemctl --user restart "$service"
        done
        print_success "Services restarted"
    else
        print_warning "You can restart them later with: systemctl --user restart <service>"
    fi
fi

# Final setup
print_status "Performing final setup..."

# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/tray_icon.py

# Create log directory
mkdir -p logs

print_success "Installation completed successfully!"
echo
echo "🎉 Voxtral Agentic Voice Platform is ready!"
echo "============================================"
echo
echo "📋 Next steps:"
echo "1. Start the VLLM server:"
echo "   vllm serve mistralai/Voxtral-Mini-3B-2507 --tokenizer_mode mistral --config_format mistral --load_format mistral"
echo
echo "2. Launch the tray application:"
echo "   ./venv/bin/python scripts/tray_icon.py"
echo
echo "3. Or run the agent directly:"
echo "   ./venv/bin/python agent/agent_main.py"
echo
echo "📁 Configuration file: config/voxtral.yaml"
echo "📋 Logs will be written to: voxtral.log"
echo
if [[ ${#SERVICES_TO_RESTART[@]} -gt 0 && ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "⚠️  Remember to restart audio services or log out/in for optimal performance"
fi

# Check if logout is recommended
if groups | grep -q audio; then
    print_success "Audio group membership confirmed"
else
    print_warning "⚠️  You may need to log out and back in for audio group changes to take effect"
fi

echo
print_success "Happy voice commanding! 🎙️"
