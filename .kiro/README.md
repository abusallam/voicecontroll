# .kiro Folder Documentation

This folder contains comprehensive project context and automation for the Voxtral Voice Platform, designed to enhance development workflow with Kiro IDE.

## 📁 Folder Structure

```
.kiro/
├── steering/           # Project context and conventions
│   ├── product.md      # Product vision and current status
│   ├── tech.md         # Technology stack and dependencies
│   ├── structure.md    # Project organization and patterns
│   ├── development.md  # Development workflow and guidelines
│   ├── testing.md      # Testing protocols and procedures
│   └── project-status.md # Current project state and roadmap
├── specs/              # Structured planning artifacts
│   ├── voice-platform-stability-enhancements/
│   │   ├── requirements.md # User stories and acceptance criteria
│   │   ├── design.md       # Technical architecture and interfaces
│   │   └── tasks.md        # Actionable implementation steps
│   └── voice-platform-enhancements/
│       ├── requirements.md # Future enhancement requirements
│       ├── design.md       # Enhancement design documents
│       └── tasks.md        # Enhancement implementation tasks
├── hooks/              # Event-driven automation
│   ├── test-on-save.md     # Auto-test when files change
│   ├── update-docs.md      # Auto-update documentation
│   └── security-check.md   # Pre-commit security scanning
└── README.md           # This documentation file
```

## 🎯 Purpose and Benefits

### Steering Files (Always Loaded)
- **Consistent Context**: Kiro understands the project without re-explanation
- **Team Alignment**: Shared understanding of conventions and patterns
- **Institutional Memory**: Preserves decisions and rationale across sessions

### Specs (Structured Planning)
- **Requirements → Design → Tasks**: Complete development lifecycle
- **Auditable History**: All planning decisions in version control
- **Task Integration**: Direct links to implementation actions

### Hooks (Event-Driven Automation)
- **Quality Assurance**: Automatic testing and validation
- **Documentation Sync**: Keep docs current with code changes
- **Security Enforcement**: Prevent credential leaks and vulnerabilities

## 🚀 How to Use This Documentation

### For New Development Sessions
1. **Review `steering/project-status.md`** - Understand current state
2. **Check `specs/*/tasks.md`** - See what's planned or in progress
3. **Follow `steering/development.md`** - Use established workflow patterns

### For Feature Development
1. **Create new spec** in `specs/feature-name/`
2. **Follow Requirements → Design → Tasks** progression
3. **Use hooks** for automated quality checks

### For Maintenance and Debugging
1. **Consult `steering/testing.md`** - Use proven testing protocols
2. **Reference `steering/development.md`** - Follow troubleshooting guides
3. **Check `specs/*/design.md`** - Understand architectural decisions

## 📋 Current Project State (Quick Reference)

### ✅ Stable Release 1.0.0 (Production Ready)
- **Main App**: `scripts/voxtral_tray_stable.py`
- **Status**: All core features working and tested
- **GitHub**: https://github.com/abusallam/voicecontroll.git
- **Performance**: 300-800ms typing, ~1GB memory, stable operation

### 🎯 Core Features (Working)
- Quick Record (5s) with cursor typing
- Continuous Dictation with voice activity detection
- System Tray with GTK integration
- Auto-startup with systemd service
- Global Hotkeys (Ctrl+Alt)
- Service Management (folder navigation)
- Enhanced Cursor Typing (multiple fallbacks)

### 🔧 Essential Commands
```bash
# Start application
uv run scripts/voxtral_tray_stable.py

# Kill all processes (ALWAYS do this first)
uv run scripts/kill_tray.py

# Run system test
uv run scripts/test_system.py

# Setup autostart
bash scripts/setup_autostart.sh
```

### ⚠️ Critical Development Rules
1. **ALWAYS kill existing processes** before starting new ones
2. **Test step-by-step** - one feature at a time
3. **Use system test** for validation
4. **Check process status** before and after changes

## 🔮 Future Development Phases

### Phase 2: Enhancements (Next)
- Improve transcription accuracy
- Add model selection UI
- Implement configuration interface
- Better voice activity detection

### Phase 3: AI Integration (Future)
- VLLM server integration
- LangGraph workflow orchestration
- AI agent capabilities
- Advanced tool execution

## 📞 Support and Maintenance

### Documentation Updates
- **Always update** relevant steering files when making changes
- **Keep specs current** with actual implementation
- **Update project-status.md** after major milestones

### Quality Assurance
- **Use established testing protocols** from `steering/testing.md`
- **Follow development guidelines** from `steering/development.md`
- **Leverage hooks** for automated quality checks

### Community Contributions
- **Reference steering files** for project context
- **Follow established patterns** for consistency
- **Update documentation** with any changes

---

**This .kiro folder represents the institutional memory and development intelligence of the Voxtral Voice Platform project. Use it to maintain consistency, quality, and efficiency across all development sessions.**