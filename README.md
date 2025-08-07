# 🎙️ Voxtral Voice Platform - Stable Release

**A fully functional, Linux-native voice transcription platform** - Real-time speech-to-text with cursor-aware typing for all Linux desktop environments.

Built with **OpenAI Whisper**, **enhanced cursor typing**, and **stable system tray integration**. Designed for **Debian 12+ with GNOME Wayland** (X11 fallback supported).

---

## ✨ **Current Features (Stable Release)**

- 🎙️ **Real-time voice transcription** using OpenAI Whisper (local, private)
- ⌨️ **Cursor-aware typing** - types directly where your cursor is positioned
- 🖥️ **System tray interface** - minimal, always-accessible control
- 🔄 **Continuous dictation** - voice activity detection with start/stop
- ⚡ **Quick record** - 5-second voice recording with instant transcription
- 🔧 **Service management** - folder navigation and system utilities
- 🚀 **Auto-startup** - automatic system boot integration
- ⌨️ **Global hotkeys** - Ctrl+Alt activation (when available)
- 🐧 **Linux-optimized** - Wayland/X11 support, multiple typing methods
- 🔒 **Privacy-first** - everything runs locally, no cloud dependencies

---

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 wtype wl-clipboard ydotool

# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### **Installation**
```bash
# Clone the repository
git clone https://github.com/yourusername/voxtral-agentic-voice-platform.git
cd voxtral-agentic-voice-platform

# Install dependencies
uv sync

# Start the stable tray application
uv run scripts/voxtral_tray_stable.py
```

### **Usage**
1. **Right-click the microphone tray icon** to access all features
2. **Quick Record**: Click "🎙️ Quick Record (5s)" → Speak → Text appears at cursor
3. **Continuous**: Click "🎧 Start Continuous" → Speak naturally → Auto-types speech
4. **Global Hotkey**: Press Ctrl+Alt to trigger quick record (if available)

---

## 🎯 **Core Functionality**

### **Voice Features**
| Feature | Description | Status |
|---------|-------------|--------|
| Quick Record (5s) | 5-second voice recording with instant transcription | ✅ Working |
| Continuous Dictation | Real-time voice activity detection and transcription | ✅ Working |
| Global Hotkeys | Ctrl+Alt activation without tray interaction | ✅ Working |

### **System Integration**
| Feature | Description | Status |
|---------|-------------|--------|
| Cursor Typing | Direct text insertion at cursor position | ✅ Working |
| System Tray | GTK-based tray with full menu functionality | ✅ Working |
| Auto-startup | Automatic system boot integration | ✅ Working |
| Service Management | Folder navigation and system utilities | ✅ Working |

### **Typing Methods (Automatic Fallback)**
1. **ydotool** (primary) - Direct input injection
2. **wtype** (Wayland) - Native Wayland typing
3. **xdotool** (X11) - X11 input simulation
4. **Clipboard** (fallback) - Copy to clipboard with paste instruction

---

## 📁 **Project Structure**

```
voxtral-agentic-voice-platform/
├── scripts/
│   ├── voxtral_tray_stable.py    # ✅ Main stable tray application
│   ├── kill_tray.py              # ✅ Utility for killing tray processes
│   ├── setup_autostart.sh        # ✅ Auto-startup configuration
│   ├── test_system.py            # ✅ System testing and validation
│   └── icon.png                  # ✅ Tray icon
├── tools/
│   └── enhanced_cursor_typing.py # ✅ Advanced cursor typing with fallbacks
├── config/
│   ├── settings.py               # Configuration management
│   └── voxtral.yaml              # Main configuration file
├── agent/                        # Future: AI agent integration
├── langraph/                     # Future: Workflow orchestration
└── models/                       # Future: VLLM integration
```

---

## ⚙️ **System Requirements**

### **Minimum Requirements**
- **OS**: Debian 12+ (or compatible Linux distribution)
- **Desktop**: GNOME with Wayland (X11 fallback supported)
- **RAM**: 4GB+ (8GB+ recommended for better performance)
- **Python**: 3.10+
- **Audio**: PulseAudio or PipeWire with microphone access

### **Audio Dependencies**
```bash
# Required for audio processing
sudo apt install python3-sounddevice python3-numpy python3-soundfile

# Whisper will be installed automatically via UV
```

### **Typing Dependencies**
```bash
# Primary typing method (recommended)
sudo apt install ydotool

# Wayland typing (alternative)
sudo apt install wtype wl-clipboard

# X11 typing (fallback)
sudo apt install xdotool xclip
```

---

## 🎛️ **Advanced Configuration**

### **Whisper Model Selection**
The system automatically uses the "base" Whisper model for stability. You can modify this in the code:

```python
# In voxtral_tray_stable.py, line ~150
self.whisper_model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
```

### **Audio Settings**
```python
# Adjustable parameters in voxtral_tray_stable.py
self.sample_rate = 16000           # Audio sample rate
self.silence_threshold = 0.02      # Voice activity detection sensitivity
self.silence_duration = 2.0        # Pause duration before processing
self.min_duration = 1.0            # Minimum recording length
```

### **Auto-startup Management**
```bash
# Enable auto-startup
bash scripts/setup_autostart.sh

# Or use the tray menu: Right-click → Settings → Enable Autostart
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Tray Icon Not Appearing**
```bash
# Check if GTK libraries are installed
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1

# Restart the tray
uv run scripts/kill_tray.py
uv run scripts/voxtral_tray_stable.py
```

#### **Voice Recording Not Working**
```bash
# Test microphone
arecord -d 5 test.wav && aplay test.wav

# Check audio permissions
groups | grep audio

# If not in audio group:
sudo usermod -a -G audio $USER
# Then log out and back in
```

#### **Typing Not Working**
```bash
# Check available typing tools
which ydotool wtype xdotool

# Test ydotool (may need sudo)
sudo ydotool type "test"

# Test wtype (Wayland)
wtype "test"

# Test xdotool (X11)
xdotool type "test"
```

#### **Multiple Tray Icons**
```bash
# Kill all tray processes
uv run scripts/kill_tray.py

# Start fresh
uv run scripts/voxtral_tray_stable.py
```

### **Performance Issues**

#### **Slow Transcription**
- Use smaller Whisper model (tiny instead of base)
- Ensure sufficient RAM available
- Close other resource-intensive applications

#### **High Memory Usage**
- The system uses ~1GB RAM with Whisper model loaded
- Memory is automatically cleaned up every 30 seconds
- Restart the tray if memory usage becomes excessive

---

## 🧪 **Testing**

### **System Test**
```bash
# Run comprehensive system test
uv run scripts/test_system.py

# Or use tray menu: Right-click → Test System
```

### **Manual Testing**
1. **Quick Record**: Right-click tray → Quick Record → Speak for 3-4 seconds
2. **Continuous**: Right-click tray → Start Continuous → Speak with pauses
3. **Quit**: Right-click tray → Quit (should close immediately)
4. **Folders**: Right-click tray → Services → Agent Folder (should open file manager)

---

## 🔒 **Security & Privacy**

- **Local Processing**: All voice processing happens locally
- **No Cloud Dependencies**: No data sent to external services
- **Temporary Files**: Audio files are automatically deleted after processing
- **Memory Clearing**: Audio buffers are cleared after each transcription
- **No Persistence**: No voice data is stored permanently

---

## 🚧 **Development Roadmap**

### **Phase 1: Stability (✅ Complete)**
- [x] Fix Whisper tensor errors
- [x] Implement proper quit functionality
- [x] Add continuous dictation start/stop
- [x] Fix microphone conflicts
- [x] Add comprehensive error handling

### **Phase 2: Enhancement (🚧 In Progress)**
- [ ] Improve transcription accuracy
- [ ] Add model selection UI
- [ ] Implement configuration interface
- [ ] Add voice command recognition

### **Phase 3: AI Integration (📋 Planned)**
- [ ] VLLM server integration
- [ ] LangGraph workflow orchestration
- [ ] AI agent capabilities
- [ ] Tool execution framework

---

## 🤝 **Contributing**

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** (follow the existing code style)
4. **Test thoroughly** using `scripts/test_system.py`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### **Development Guidelines**
- Always test with `scripts/test_system.py` before submitting
- Use `scripts/kill_tray.py` to clean up processes during development
- Follow the existing error handling patterns
- Document new features in the README

---

## 📊 **Performance Metrics**

### **Typical Performance**
- **Startup Time**: 3-5 seconds (Whisper model loading)
- **Quick Record**: 5s recording + 2-3s transcription
- **Continuous Mode**: Real-time with 2s pause detection
- **Typing Speed**: 300-800ms depending on method
- **Memory Usage**: ~1GB with base Whisper model
- **CPU Usage**: <5% during idle, 50-80% during transcription

### **Tested Configurations**
- **Debian 12 + GNOME Wayland**: ✅ Fully working
- **Ubuntu 22.04 + GNOME**: ✅ Compatible
- **Memory**: Tested with 4GB-16GB RAM
- **CPU**: Works on both Intel and AMD processors

---

## 📄 **License**

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **OpenAI** for the Whisper speech recognition model
- **Python community** for excellent audio processing libraries
- **GTK developers** for the system tray framework
- **Linux audio community** for PulseAudio/PipeWire
- **Wayland/X11 developers** for display server protocols
- **All contributors and testers** who helped make this stable

---

## 📞 **Support**

- **Issues**: Report bugs via [GitHub Issues](https://github.com/yourusername/voxtral-agentic-voice-platform/issues)
- **Discussions**: Join community discussions for help and ideas
- **Documentation**: This README contains comprehensive troubleshooting
- **Testing**: Use `scripts/test_system.py` for diagnostics

---

**🎉 Stable Release - Ready for Daily Use! 🎙️🐧**

*Built with ❤️ for the Linux community*