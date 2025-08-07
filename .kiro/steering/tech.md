# Technology Stack - Stable Release 1.0.0

## Core Technologies (Current)
- **Python 3.10+** - Primary programming language
- **OpenAI Whisper** - Speech recognition (local, private)
- **GTK 3.0** - System tray UI framework
- **sounddevice** - Audio capture and processing
- **numpy** - Audio data processing
- **UV** - Modern Python package manager

## System Dependencies (Required)
- **Debian 12+** with GNOME + Wayland (X11 fallback)
- **python3-gi** - GTK Python bindings
- **gir1.2-ayatanaappindicator3-0.1** - System tray support
- **ydotool** - Primary text injection method
- **wtype** - Wayland text injection (alternative)
- **wl-clipboard** - Wayland clipboard operations
- **xdotool** - X11 text injection (fallback)
- **xclip** - X11 clipboard operations (fallback)

## Current Architecture (Stable)
- **Main Application**: `scripts/voxtral_tray_stable.py`
- **Enhanced Cursor Typing**: `tools/enhanced_cursor_typing.py`
- **Process Management**: `scripts/kill_tray.py`
- **Auto-startup**: `scripts/setup_autostart.sh`
- **System Testing**: `scripts/test_system.py`

## Installation Commands (Current)

### System Dependencies
```bash
sudo apt update
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 wtype wl-clipboard ydotool
```

### UV Package Manager
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Project Setup
```bash
git clone https://github.com/abusallam/voicecontroll.git
cd voicecontroll
uv sync
```

### Running the Application
```bash
uv run scripts/voxtral_tray_stable.py
```

### Utility Commands
```bash
# Kill all tray processes
uv run scripts/kill_tray.py

# Run system test
uv run scripts/test_system.py

# Setup autostart
bash scripts/setup_autostart.sh
```

## Future Technologies (Planned)
- **VLLM** - Voice Language Model serving (Phase 3)
- **LangGraph** - Workflow orchestration (Phase 3)
- **Voxtral (Mistral 3B)** - Advanced voice-to-text model (Phase 3)
- **PyQt5** - Advanced UI framework (Phase 2)

## Performance Characteristics
- **Startup Time**: 3-5 seconds (Whisper model loading)
- **Memory Usage**: ~1GB with base Whisper model
- **CPU Usage**: <5% idle, 50-80% during transcription
- **Typing Latency**: 300-800ms depending on method
- **Audio Processing**: Real-time with 2s pause detection