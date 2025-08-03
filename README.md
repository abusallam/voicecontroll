# 🧠 Voxtral Agentic Voice Platform

**A comprehensive, Linux-native voice-controlled AI agent platform** - A community contribution to the Linux ecosystem that rivals commercial solutions like Wispr Flow.

Built with **Voxtral Mini 3B** via **VLLM**, **LangGraph** orchestration, **OpenAI Whisper fallback**, and **cursor-aware typing**. Designed for **all Linux desktop environments** including GNOME, KDE, XFCE, and others.

---

## ✨ Key Features

- 🎙️ **Real-time voice transcription** using Voxtral Mini 3B (local, private)
- 🧠 **Intelligent agent workflows** with LangGraph orchestration  
- ⌨️ **Cursor-aware typing** - types directly where your cursor is positioned
- 🔧 **Safe tool execution** - shell commands, web search, file operations
- 🖥️ **System tray interface** - minimal, always-accessible control
- 🐧 **Linux-optimized** - Wayland/X11 support, audio system integration
- 🔒 **Privacy-first** - everything runs locally, no cloud dependencies
- 🚀 **Low-latency** - optimized for real-time voice interaction

---

## 🚀 Quick Start

### Method 1: Install via .deb Package (Recommended)
```bash
# Download and install the .deb package
sudo dpkg -i voxtral-agentic-voice-platform_1.0.0_amd64.deb
sudo apt-get install -f  # Fix dependencies if needed

# Enable auto-startup
voxtral-setup-autostart

# Start the tray interface
voxtral-tray
```

### Method 2: Install from Source with UV
```bash
# Install UV package manager if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/voicecontroll/voxtral-agentic-voice-platform.git
cd voxtral-agentic-voice-platform
chmod +x scripts/install_uv.sh
./scripts/install_uv.sh

# Start the system
uv run scripts/voxtral_tray_gtk.py
```

### 3. Test the System
```bash
voxtral-test  # If installed via .deb
# OR
uv run scripts/test_system.py  # If installed from source
```

### 4. Use Voice Commands
- **Speak naturally** → Text appears in clipboard → **Press Ctrl+V** to paste at cursor
- **"Search for Python tutorials"** → Web search
- **"Run ls -la"** → Execute shell command  
- **"Open github.com"** → Open URL in browser

**Note:** On GNOME Wayland, voice transcription copies text to clipboard. Press Ctrl+V to paste at your cursor position.

---

## 🎯 Usage Examples

| Voice Command | Action |
|---------------|--------|
| "Type hello world" | Types "hello world" at cursor position |
| "Search for Python tutorials" | Opens web search results |
| "Run ls -la" | Executes shell command safely |
| "Open github.com" | Opens URL in default browser |
| "What's the weather like?" | Searches and summarizes weather info |

---

## 📁 Project Structure

```
├── agent/              # Voice processing & agent logic
│   ├── agent_main.py   # Main agent orchestrator
│   ├── voice_processor.py # Audio capture & VAD
│   └── prompts/        # System prompts & behavior
├── tools/              # Agent tools & capabilities
│   ├── shell.py        # Safe shell command execution
│   ├── web_search.py   # DuckDuckGo search integration
│   └── cursor_typing.py # Wayland/X11 text injection
├── langraph/           # Workflow orchestration
│   └── workflows.py    # LangGraph agent workflows
├── models/             # VLLM integration
│   └── vllm_handler.py # OpenAI-compatible API client
├── config/             # Configuration management
│   ├── settings.py     # Configuration loader
│   └── voxtral.yaml    # Main configuration file
└── scripts/            # Installation & UI
    ├── install.sh      # Automated setup script
    └── tray_icon.py    # PyQt5 system tray interface
```

---

## ⚙️ Configuration

Edit `config/voxtral.yaml` to customize:

```yaml
# Voice processing
voice:
  hush_word: "__stop__"        # Stop recording trigger
  silence_duration: 2.0        # Seconds before auto-stop
  continuous_mode: true        # Always listening vs push-to-talk

# Model settings  
model:
  temperature_transcription: 0.0  # Deterministic transcription
  temperature_chat: 0.2          # Slightly creative responses
  
# System integration
system:
  cursor_injection: true       # Enable typing at cursor
  display_server: "wayland"    # wayland or x11
```

---

## 🔧 System Requirements

- **OS**: Debian 12+ (or compatible Linux)
- **Desktop**: GNOME with Wayland (X11 fallback supported)
- **GPU**: NVIDIA with 10GB+ VRAM (CPU inference available)
- **RAM**: 16GB+ recommended
- **Python**: 3.10+

### Audio Dependencies
- PulseAudio or PipeWire
- Low-latency audio configuration
- Microphone access permissions

### Wayland Tools
- `wtype` - Keyboard input simulation
- `wl-clipboard` - Clipboard operations

### X11 Fallback
- `xdotool` - Legacy input simulation  
- `xclip` - X11 clipboard operations

---

## 🛡️ Security Features

- **Safe command execution** - Whitelist of allowed commands only
- **No root access** - Agent cannot execute sudo/privileged commands  
- **Local processing** - No data sent to external services
- **Sandboxed tools** - Each tool runs in isolated environment
- **Audit logging** - All actions logged for security review

---

## 🎛️ Advanced Features

### Voice Activity Detection
- WebRTC VAD for accurate speech detection
- Energy-based fallback for robustness
- Configurable silence thresholds
- Hush word support for immediate stop

### Context Awareness
- Intent detection (typing, commands, search)
- Cursor position awareness
- Application context integration
- Conversation memory

### Tool Orchestration
- LangGraph-based workflow engine
- Conditional tool selection
- Error handling and retry logic
- Async tool execution

---

## 🔍 Troubleshooting

### Audio Issues
```bash
# Check audio permissions
groups | grep audio

# Restart PulseAudio
systemctl --user restart pulseaudio

# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

### VLLM Connection
```bash
# Check if server is running
curl http://localhost:8000/v1/models

# Check GPU memory
nvidia-smi
```

### Typing Not Working
```bash
# Wayland: Check wtype
which wtype

# X11: Check xdotool  
which xdotool

# Test typing manually
wtype "test text"
```

---

## 🚧 Development

### Adding Custom Tools
1. Create tool function with `@tool` decorator
2. Register in `langraph/workflows.py`
3. Add schema for parameters
4. Update system prompts

### Extending Workflows
- Modify `VoxtralWorkflow` class
- Add new LangGraph nodes
- Implement custom state logic
- Configure routing conditions

---

## 📊 Performance

- **Transcription Latency**: <500ms typical
- **Response Generation**: 1-3s depending on complexity
- **Memory Usage**: ~8GB with model loaded
- **CPU Usage**: <10% during idle listening
- **GPU Utilization**: 60-80% during inference

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Community Contribution

This project is **proudly contributed to the Linux community** as an open-source alternative to commercial voice control solutions. It's designed to work across **all Linux desktop environments** and can be easily adapted for different setups.

### 🖥️ Multi-Desktop Environment Support

The platform is designed to work seamlessly across different Linux desktop environments:

- **GNOME** (Wayland/X11) - Primary development target
- **KDE Plasma** (Wayland/X11) - Full compatibility
- **XFCE** - X11 support with xdotool
- **MATE** - X11 support
- **Cinnamon** - X11 support
- **i3/Sway** - Wayland (Sway) and X11 (i3) tiling window managers
- **Custom setups** - Easily adaptable

### 🔧 Adapting for Your Environment

To adapt this system for your specific desktop environment:

1. **Audio System**: The platform auto-detects PulseAudio/PipeWire
2. **Display Server**: Automatically chooses Wayland (wtype) or X11 (xdotool) tools
3. **Tray Integration**: PyQt5 system tray works across all desktop environments
4. **Customization**: Edit `config/voxtral.yaml` for your specific setup

### 🤝 Community Goals

- **Open Source**: Fully open and free for all Linux users
- **Privacy-First**: No telemetry, no cloud dependencies
- **Extensible**: Easy to add new tools and capabilities
- **Inclusive**: Works on low-end hardware with CPU-only mode
- **Educational**: Well-documented for learning and contribution

---

## 🚀 CPU-Only & Fallback Support

This platform includes comprehensive fallback support for systems without powerful GPUs:

### 🖥️ CPU-Only VLLM
- Automatic CPU detection and configuration
- Optimized settings for CPU inference
- Reduced memory requirements

### 🎙️ OpenAI Whisper Fallback
- Automatic fallback if VLLM transcription fails
- Local Whisper model (no internet required)
- Multiple model sizes (base, small, medium, large)

### 🔄 Graceful Degradation
1. **First**: Try VLLM with GPU acceleration
2. **Second**: Fall back to VLLM CPU-only mode
3. **Third**: Use mock server for testing
4. **Transcription**: VLLM → OpenAI Whisper → Error handling

---

## 🙏 Acknowledgments

- **Community Contributor**: This project is a contribution to the Linux community
- **Mistral AI** for the Voxtral model
- **vLLM team** for the inference engine
- **LangChain/LangGraph** for workflow orchestration
- **OpenAI** for Whisper speech recognition
- **Linux audio community** for PulseAudio/PipeWire
- **Wayland developers** for modern display protocols
- **All Linux desktop environment maintainers** for creating diverse, open ecosystems

---

## 📞 Support & Community

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions for help and ideas
- **Contributions**: All contributions welcome - from bug fixes to new features
- **Documentation**: Help improve docs for better community adoption

---

**Built with ❤️ for the Linux community! 🐧🎙️**
