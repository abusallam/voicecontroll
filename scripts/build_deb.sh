#!/bin/bash
set -e

echo "📦 Building Voxtral .deb Package"
echo "================================"

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

# Get project info
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_NAME="voxtral-agentic-voice-platform"
VERSION="1.0.0"
ARCH="amd64"

print_status "Project root: $PROJECT_ROOT"
print_status "Package: $PACKAGE_NAME"
print_status "Version: $VERSION"
print_status "Architecture: $ARCH"

# Create build directory
BUILD_DIR="$PROJECT_ROOT/build"
PACKAGE_DIR="$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}"

print_status "Creating build directory: $PACKAGE_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$PACKAGE_DIR"

# Create directory structure
mkdir -p "$PACKAGE_DIR/DEBIAN"
mkdir -p "$PACKAGE_DIR/opt/voxtral"
mkdir -p "$PACKAGE_DIR/usr/bin"
mkdir -p "$PACKAGE_DIR/usr/share/applications"
mkdir -p "$PACKAGE_DIR/usr/share/pixmaps"

# Copy control files
cp "$PROJECT_ROOT/debian/control" "$PACKAGE_DIR/DEBIAN/"
cp "$PROJECT_ROOT/debian/postinst" "$PACKAGE_DIR/DEBIAN/"

# Copy application files
print_status "Copying application files..."
cp -r "$PROJECT_ROOT/agent" "$PACKAGE_DIR/opt/voxtral/"
cp -r "$PROJECT_ROOT/config" "$PACKAGE_DIR/opt/voxtral/"
cp -r "$PROJECT_ROOT/langraph" "$PACKAGE_DIR/opt/voxtral/"
cp -r "$PROJECT_ROOT/models" "$PACKAGE_DIR/opt/voxtral/"
cp -r "$PROJECT_ROOT/scripts" "$PACKAGE_DIR/opt/voxtral/"
cp -r "$PROJECT_ROOT/tools" "$PACKAGE_DIR/opt/voxtral/"
cp "$PROJECT_ROOT/pyproject.toml" "$PACKAGE_DIR/opt/voxtral/"
cp "$PROJECT_ROOT/requirements.txt" "$PACKAGE_DIR/opt/voxtral/"
cp "$PROJECT_ROOT/README.md" "$PACKAGE_DIR/opt/voxtral/"
cp "$PROJECT_ROOT/LICENSE" "$PACKAGE_DIR/opt/voxtral/"

# Create wrapper scripts
print_status "Creating wrapper scripts..."

cat > "$PACKAGE_DIR/usr/bin/voxtral-tray" << 'EOF'
#!/bin/bash
cd /opt/voxtral
if [ ! -d ".venv" ]; then
    echo "🔧 Setting up Python environment..."
    uv sync
fi
.venv/bin/python scripts/voxtral_tray_gtk.py "$@"
EOF

cat > "$PACKAGE_DIR/usr/bin/voxtral-test" << 'EOF'
#!/bin/bash
cd /opt/voxtral
if [ ! -d ".venv" ]; then
    echo "🔧 Setting up Python environment..."
    uv sync
fi
.venv/bin/python scripts/test_system.py "$@"
EOF

cat > "$PACKAGE_DIR/usr/bin/voxtral-setup-autostart" << 'EOF'
#!/bin/bash
cd /opt/voxtral
if [ ! -d ".venv" ]; then
    echo "🔧 Setting up Python environment..."
    uv sync
fi
./scripts/setup_autostart.sh "$@"
EOF

cat > "$PACKAGE_DIR/usr/bin/voxtral-cursor-test" << 'EOF'
#!/bin/bash
cd /opt/voxtral
if [ ! -d ".venv" ]; then
    echo "🔧 Setting up Python environment..."
    uv sync
fi
.venv/bin/python scripts/test_cursor_typing.py "$@"
EOF

chmod +x "$PACKAGE_DIR/usr/bin/"*

# Create desktop entry
cat > "$PACKAGE_DIR/usr/share/applications/voxtral.desktop" << EOF
[Desktop Entry]
Name=Voxtral Voice Agent
Comment=AI-powered voice assistant for Linux
Exec=voxtral-tray
Icon=voxtral
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
StartupNotify=true
EOF

# Copy icon
if [ -f "$PROJECT_ROOT/scripts/icon.png" ]; then
    cp "$PROJECT_ROOT/scripts/icon.png" "$PACKAGE_DIR/usr/share/pixmaps/voxtral.png"
else
    print_warning "Icon not found, creating placeholder"
    # Create a simple placeholder icon
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" | base64 -d > "$PACKAGE_DIR/usr/share/pixmaps/voxtral.png"
fi

# Set permissions
find "$PACKAGE_DIR" -type f -exec chmod 644 {} \;
find "$PACKAGE_DIR" -type d -exec chmod 755 {} \;
chmod +x "$PACKAGE_DIR/DEBIAN/postinst"
chmod +x "$PACKAGE_DIR/usr/bin/"*
chmod +x "$PACKAGE_DIR/opt/voxtral/scripts/"*.sh
chmod +x "$PACKAGE_DIR/opt/voxtral/scripts/"*.py

# Build the package
print_status "Building .deb package..."
dpkg-deb --build "$PACKAGE_DIR"

# Move to final location
FINAL_PACKAGE="$PROJECT_ROOT/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
mv "$PACKAGE_DIR.deb" "$FINAL_PACKAGE"

print_success "Package built successfully: $FINAL_PACKAGE"
print_status "Package size: $(du -h "$FINAL_PACKAGE" | cut -f1)"

echo
echo "📦 Installation commands:"
echo "  sudo dpkg -i $FINAL_PACKAGE"
echo "  sudo apt-get install -f  # Fix dependencies if needed"
echo
echo "🚀 Usage after installation:"
echo "  voxtral-tray              # Start tray interface"
echo "  voxtral-test              # Run system tests"
echo "  voxtral-setup-autostart   # Enable auto-startup"
echo "  voxtral-cursor-test       # Test cursor typing"
echo
print_success "Ready for distribution! 🎉"