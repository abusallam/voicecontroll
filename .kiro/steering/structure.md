# Project Structure - Stable Release 1.0.0

## Current Directory Organization (Production Ready)

The project follows a clean, modular structure optimized for the stable voice platform:

```
voxtral-agentic-voice-platform/
├── scripts/                    # Core application and utilities
│   ├── voxtral_tray_stable.py # ✅ Main stable tray application
│   ├── kill_tray.py           # ✅ Process management utility
│   ├── setup_autostart.sh     # ✅ Auto-startup configuration
│   ├── test_system.py         # ✅ System testing and validation
│   └── icon.png               # ✅ Tray icon asset
├── tools/                      # Enhanced functionality
│   └── enhanced_cursor_typing.py # ✅ Advanced cursor typing with fallbacks
├── config/                     # Configuration management
│   ├── settings.py            # Configuration loader
│   └── voxtral.yaml           # Main configuration file
├── agent/                      # Future: AI agent integration
├── langraph/                   # Future: Workflow orchestration
├── models/                     # Future: VLLM integration
└── docs/                       # Project documentation
```

## Key Conventions (Current)

### Scripts Directory (`scripts/`) - Core Application
- **`voxtral_tray_stable.py`** - Main production-ready tray application
- **`kill_tray.py`** - Essential utility for process management
- **`setup_autostart.sh`** - Systemd service integration
- **`test_system.py`** - Comprehensive system validation
- **`icon.png`** - System tray icon asset

### Tools Directory (`tools/`) - Enhanced Features
- **`enhanced_cursor_typing.py`** - Multi-method cursor typing with fallbacks
- Modular design with comprehensive error handling
- Multiple typing methods: ydotool → wtype → xdotool → clipboard

### Config Directory (`config/`) - Settings Management
- **`settings.py`** - Configuration loading and validation
- **`voxtral.yaml`** - Main configuration file
- Environment-aware configuration (Wayland/X11 detection)

### Future Directories (Planned)
- **`agent/`** - AI agent integration (Phase 3)
- **`langraph/`** - Workflow orchestration (Phase 3)
- **`models/`** - VLLM integration (Phase 3)

## File Naming Conventions

### Python Files
- Use lowercase with underscores: `voxtral_tray_stable.py`
- Descriptive names indicating purpose: `enhanced_cursor_typing.py`
- Utility scripts prefixed appropriately: `kill_tray.py`

### Shell Scripts
- Use `.sh` extension: `setup_autostart.sh`
- Executable permissions: `chmod +x scripts/*.sh`
- Clear, action-oriented names

### Configuration Files
- YAML for main config: `voxtral.yaml`
- Python for complex config: `settings.py`
- Environment-specific naming when needed

### Documentation
- Markdown format: `.md`
- Descriptive names: `PROJECT_STATUS.md`, `SESSION_SUMMARY.md`
- Comprehensive README files

## Development Workflow Patterns

### Testing Protocol
1. Always kill existing processes: `uv run scripts/kill_tray.py`
2. Test step-by-step, one feature at a time
3. Use system test: `uv run scripts/test_system.py`
4. Check process status: `ps aux | grep voxtral`

### Code Organization
- Main functionality in `scripts/voxtral_tray_stable.py`
- Utilities separated into focused modules
- Enhanced features in `tools/` directory
- Configuration centralized in `config/`

### Version Control
- Clean commits with descriptive messages
- Tag stable releases: `v1.0.0-stable`
- Comprehensive .gitignore for Python projects
- Documentation updated with code changes

## Architecture Patterns (Current)

### GTK System Tray Pattern
- Main application class: `VoxtralStableTray`
- Menu-driven interface with right-click access
- Thread-safe GTK operations using `GLib.idle_add`
- Proper resource cleanup and shutdown handling

### Audio Processing Pattern
- Voice activity detection with configurable thresholds
- Buffer management with limits and cleanup
- Error recovery without crashes
- Temporary file handling with automatic cleanup

### Cursor Typing Pattern
- Multiple fallback methods for maximum compatibility
- Performance optimization with reduced timeouts
- Comprehensive error handling and logging
- Cross-platform support (Wayland/X11)

### Process Management Pattern
- External kill utility for robust process management
- Systemd service integration for auto-startup
- Status monitoring and health checks
- Clean shutdown procedures