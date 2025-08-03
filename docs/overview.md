# Voxtral Agentic Voice Platform - Technical Overview

## Architecture

The Voxtral platform is a comprehensive voice-controlled AI agent system designed specifically for Linux environments. It combines local speech recognition, AI reasoning, and system integration to provide a powerful voice interface.

### Core Components

#### 1. Voice Processing (`agent/voice_processor.py`)
- **Real-time audio capture** using sounddevice
- **Voice Activity Detection (VAD)** with WebRTC VAD and energy-based detection
- **Silence detection** with configurable thresholds and hush word support
- **Streaming audio processing** with circular buffers for efficiency
- **Push-to-talk and continuous modes** for different usage patterns

#### 2. VLLM Handler (`models/vllm_handler.py`)
- **OpenAI-compatible API client** for Voxtral model interaction
- **Audio transcription** via `/audio/transcriptions` endpoint
- **Chat completion** with tool calling support
- **Tool execution orchestration** with async support
- **Error handling and retry logic** for robust operation

#### 3. LangGraph Workflows (`langraph/workflows.py`)
- **State-based agent orchestration** using LangGraph
- **Context-aware processing** with intent detection
- **Tool selection and execution** based on user input
- **Conversation flow management** with message history
- **Response generation and formatting** for different output types

#### 4. Tool System (`tools/`)
- **Shell execution** (`shell.py`) - Safe command execution with security restrictions
- **Web search** (`web_search.py`) - DuckDuckGo integration for web and news search
- **Cursor typing** (`cursor_typing.py`) - Wayland/X11 text injection at cursor position
- **URL handling** - Browser integration for web content access

#### 5. System Tray Interface (`scripts/tray_icon.py`)
- **PyQt5-based system tray** with context menu controls
- **Process management** for agent and VLLM server
- **Status monitoring** with real-time updates
- **Configuration access** and log file management
- **Desktop integration** with folder shortcuts

## Technical Specifications

### Audio Processing
- **Sample Rate**: 16kHz (configurable)
- **Channels**: Mono (1 channel)
- **Chunk Size**: 1024 samples
- **VAD Aggressiveness**: Level 2 (0-3 scale)
- **Silence Threshold**: 0.01 RMS energy
- **Silence Duration**: 2.0 seconds before stopping

### Model Configuration
- **Primary Model**: mistralai/Voxtral-Mini-3B-2507
- **Transcription Temperature**: 0.0 (deterministic)
- **Chat Temperature**: 0.2 (slightly creative)
- **Top-p**: 0.95
- **Max Tokens**: 2048
- **GPU Memory Utilization**: 80%

### System Requirements
- **OS**: Debian 12 (or compatible Linux distribution)
- **Desktop**: GNOME with Wayland (X11 fallback supported)
- **GPU**: NVIDIA with 10GB+ VRAM (CPU fallback available)
- **RAM**: 16GB+ recommended
- **Python**: 3.10+

## Installation and Setup

### Automated Installation
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

The installation script handles:
- System package installation (audio, Wayland tools, etc.)
- Python virtual environment creation
- PyTorch installation with GPU support detection
- Audio system configuration for low latency
- Desktop integration setup
- Service configuration recommendations

### Manual VLLM Server Start
```bash
vllm serve mistralai/Voxtral-Mini-3B-2507 \
  --tokenizer_mode mistral \
  --config_format mistral \
  --load_format mistral
```

### Application Launch
```bash
# Tray interface (recommended)
python scripts/tray_icon.py

# Direct agent execution
python agent/agent_main.py
```

## Configuration

### Main Configuration (`config/voxtral.yaml`)
- **VLLM endpoint** and model settings
- **Voice processing** parameters
- **Tool availability** and permissions
- **System integration** options
- **Logging and debug** settings

### Audio Configuration
- **PulseAudio optimization** for low latency
- **Sample format and rate** configuration
- **Buffer size tuning** for real-time processing

## Security Features

### Command Execution Safety
- **Whitelist approach** for safe commands
- **Blacklist blocking** of dangerous operations
- **No sudo/root access** from voice commands
- **Sandboxed execution** environment
- **Timeout protection** against hanging processes

### Privacy Protection
- **Local-only processing** - no cloud services
- **Audio data isolation** - no persistent storage
- **Conversation logging** with configurable retention
- **Tool usage auditing** for security monitoring

## Linux-Specific Features

### Wayland Integration
- **wtype** for keyboard input simulation
- **wl-clipboard** for clipboard operations
- **Wayland security model** compliance
- **Multi-monitor support** with cursor awareness

### X11 Fallback
- **xdotool** for legacy X11 systems
- **xclip** for clipboard operations
- **Window manager integration** for focus handling

### Audio System Support
- **PulseAudio** primary support
- **PipeWire** compatibility
- **ALSA** low-level access when needed
- **Real-time scheduling** for audio threads

## Performance Optimization

### Audio Processing
- **Circular buffers** for efficient memory usage
- **Multi-threaded processing** for real-time performance
- **VAD optimization** to reduce false positives
- **Silence detection tuning** for natural conversation flow

### Model Inference
- **GPU acceleration** with VLLM
- **Batch processing** for efficiency
- **Memory management** with configurable limits
- **Caching strategies** for repeated queries

### System Integration
- **Lazy loading** of heavy components
- **Process isolation** for stability
- **Resource monitoring** and cleanup
- **Graceful degradation** when resources are limited

## Troubleshooting

### Common Issues
1. **Audio not working**: Check PulseAudio configuration and permissions
2. **VLLM server connection**: Verify server is running and accessible
3. **Typing not working**: Ensure wtype/xdotool is installed and permissions are correct
4. **GPU not detected**: Check CUDA/ROCm installation and drivers

### Debug Mode
Enable debug logging in `config/voxtral.yaml`:
```yaml
debug: true
log_level: "DEBUG"
```

### Log Analysis
- **Main log**: `voxtral.log` in project root
- **Component logs**: Separate loggers for each module
- **Error tracking**: Structured error reporting with context

## Extension and Customization

### Adding New Tools
1. Create tool function with `@tool` decorator
2. Register with VLLM handler in workflow setup
3. Add tool schema for parameter validation
4. Update system prompts for tool awareness

### Custom Workflows
- Extend `VoxtralWorkflow` class
- Add new nodes and edges to LangGraph
- Implement custom state management
- Configure conditional routing logic

### Integration APIs
- **REST API** for external tool integration
- **WebSocket** for real-time communication
- **Plugin system** for modular extensions
- **Configuration hooks** for runtime customization

## Future Roadmap

### Planned Features
- **Multi-language support** with automatic detection
- **Custom wake word** training and detection
- **Voice synthesis** for audio responses
- **Context learning** from user corrections
- **IDE integration** for development workflows

### Performance Improvements
- **Model quantization** for lower memory usage
- **Streaming inference** for reduced latency
- **Edge optimization** for resource-constrained systems
- **Distributed processing** for multi-device setups