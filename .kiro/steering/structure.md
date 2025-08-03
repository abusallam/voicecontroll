# Project Structure

## Directory Organization

The project follows a modular structure with clear separation of concerns:

```
├── agent/          # Agent prompts, logic, memory, and planning
├── tools/          # Shell tools and voice triggers
├── langraph/       # LangGraph workflow definitions
├── models/         # VLLM and Voxtral model configurations
├── scripts/        # Installation and UI scripts
│   ├── install.sh  # Automated dependency installation
│   ├── tray_icon.py # System tray application
│   └── icon.png    # Tray icon asset
└── docs/           # Project documentation
```

## Key Conventions

### Agent Directory (`agent/`)
- Contains prompts, logic, memory, and planning components
- Uses `agent/context/` folder for document-based context integration
- Follows Claude-compatible system prompt format

### Tools Directory (`tools/`)
- Houses shell tools and voice trigger implementations
- Uses directory-based activation system
- Tools should be modular and independently executable

### Scripts Directory (`scripts/`)
- Entry point scripts and utilities
- `tray_icon.py` serves as the main UI application
- `install.sh` handles automated setup
- Assets like `icon.png` for UI components

### LangGraph Directory (`langraph/`)
- Workflow orchestration and agent coordination
- Should integrate with both agent prompts and tools

## File Naming
- Use lowercase with underscores for Python files
- Shell scripts use `.sh` extension
- Configuration files follow service-specific conventions
- Documentation uses `.md` format