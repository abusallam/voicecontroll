# Development Guidelines - Voxtral Voice Platform

## Development Workflow (Established)

### Session Start Protocol
1. **Check git status**: `git status` - should be clean
2. **Kill existing processes**: `uv run scripts/kill_tray.py`
3. **Run system test**: `uv run scripts/test_system.py`
4. **Start fresh**: `uv run scripts/voxtral_tray_stable.py`

### Testing Protocol (Critical)
- **ALWAYS kill existing processes** before starting new ones
- **Test step-by-step** - one feature at a time
- **Check process status** - `ps aux | grep voxtral`
- **Use system test** for validation

### Code Quality Standards

#### Error Handling
- Comprehensive try-catch blocks for all operations
- Graceful degradation when features fail
- Clear error messages with actionable suggestions
- No crashes - log errors and continue

#### Performance Requirements
- Startup time: < 5 seconds
- Typing latency: < 1 second
- Memory usage: < 1.5GB stable
- CPU usage: < 10% idle

#### Threading Safety
- Use `GLib.idle_add` for GTK operations from threads
- Proper thread cleanup on shutdown
- Avoid race conditions in audio processing
- Clean resource management

### File Organization Principles

#### Core Files (Never Remove)
- `scripts/voxtral_tray_stable.py` - Main application
- `scripts/kill_tray.py` - Process management
- `tools/enhanced_cursor_typing.py` - Cursor typing
- `scripts/setup_autostart.sh` - Auto-startup

#### Utility Files
- `scripts/test_system.py` - System validation
- `config/settings.py` - Configuration management
- Documentation files (README, PROJECT_STATUS, etc.)

#### Development Files
- Test scripts in `scripts/test_*.py`
- Backup files should be removed after validation
- Old implementations should be cleaned up

## Common Issues and Solutions

### Multiple Tray Icons
**Problem**: Multiple instances running simultaneously
**Solution**: Always use `uv run scripts/kill_tray.py` before starting
**Prevention**: Check `ps aux | grep voxtral` before starting new instances

### Quit Function Not Working
**Problem**: GTK main loop not responding to quit
**Solution**: Use aggressive shutdown with `os._exit(0)`
**Implementation**: Already fixed in stable version

### Audio Processing Errors
**Problem**: Whisper tensor reshape errors
**Solution**: Remove problematic parameters (best_of, beam_size, patience)
**Prevention**: Use conservative audio settings

### Typing Performance Issues
**Problem**: Slow cursor typing with long timeouts
**Solution**: Reduce timeouts and implement fast fallbacks
**Implementation**: ydotool (3s) → wtype (2s) → clipboard (immediate)

## Development Phases

### Current: Stable Release 1.0.0 ✅
- All core features working and tested
- Production-ready with comprehensive error handling
- Clean codebase with proper documentation

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

## Code Review Checklist

### Before Committing
- [ ] All tests pass (`uv run scripts/test_system.py`)
- [ ] No multiple tray instances running
- [ ] Error handling is comprehensive
- [ ] Performance meets requirements
- [ ] Documentation is updated
- [ ] Security check passed

### Before Pushing
- [ ] Clean git history with descriptive commits
- [ ] All obsolete files removed
- [ ] README reflects current functionality
- [ ] No sensitive information in code
- [ ] Version tags applied for releases

## Debugging Guidelines

### Audio Issues
```bash
# Test microphone
arecord -d 5 test.wav && aplay test.wav

# Check audio permissions
groups | grep audio

# Check PulseAudio
systemctl --user status pulseaudio
```

### GTK Issues
```bash
# Check GTK libraries
dpkg -l | grep python3-gi

# Test GTK availability
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('GTK OK')"
```

### Typing Issues
```bash
# Test typing tools
which ydotool wtype xdotool
sudo ydotool type "test"
wtype "test"
```

### Process Management
```bash
# Check running processes
ps aux | grep voxtral

# Kill all instances
uv run scripts/kill_tray.py

# Check systemd service
systemctl --user status voxtral-tray.service
```