# Technology Stack

## Core Technologies
- **Python 3.10+** - Primary programming language
- **VLLM** - Voice Language Model serving
- **Voxtral (Mistral 3B)** - Voice-to-text model
- **LangGraph** - Workflow orchestration
- **PyQt5** - System tray UI framework
- **faster-whisper** - Speech recognition
- **ffmpeg** - Audio processing

## System Dependencies
- **Debian 12** with GNOME + Wayland
- **xdg-utils** - Desktop integration (`xdg-open`)
- **Python 3 pip** - Package management

## Common Commands

### Installation
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

### Running the Application
```bash
python3 scripts/tray_icon.py
```

### Manual Dependency Installation
```bash
sudo apt update
sudo apt install -y python3 python3-pip ffmpeg xdg-utils
pip3 install vllm pyqt5 langgraph faster-whisper
```

## Architecture Patterns
- Directory-based tool activation
- Claude-compatible system prompts
- Function call-based tool usage
- Context folder integration (`agent/context/`)
- Modular folder structure for agents, tools, and workflows