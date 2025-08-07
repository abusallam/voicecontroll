# Design Document

## Overview

This design addresses three critical issues in the Voxtral Agentic Voice Platform:

1. **Duplicate Service Resolution**: Eliminate conflicts between systemd and desktop autostart methods
2. **Global Hotkey Integration**: Add Ctrl+Alt hotkey activation for seamless voice input
3. **Enhanced Cursor Typing**: Improve text insertion at cursor position with better fallback mechanisms

The solution maintains backward compatibility while providing a more robust and user-friendly experience.

## Architecture

### Service Management Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Manager                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Instance Check  │    │ Startup Method  │                │
│  │ - PID detection │    │ - Systemd       │                │
│  │ - Port scanning │    │ - Desktop       │                │
│  │ - Process kill  │    │ - Manual        │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Hotkey System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Global Hotkey Manager                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Key Listener    │    │ Voice Controller│                │
│  │ - pynput        │    │ - Start/Stop    │                │
│  │ - Ctrl+Alt      │    │ - Status Track  │                │
│  │ - Background    │    │ - Feedback      │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Enhanced Cursor Typing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Cursor Typing System                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Window Detection│    │ Text Injection  │                │
│  │ - Active window │    │ - Direct type   │                │
│  │ - App context   │    │ - Clipboard     │                │
│  │ - Cursor pos    │    │ - Fallback      │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Service Manager Component

**Purpose**: Prevent duplicate instances and manage service lifecycle

**Key Classes**:
- `ServiceManager`: Main orchestrator
- `InstanceDetector`: Find existing processes
- `StartupController`: Manage autostart methods

**Interfaces**:
```python
class ServiceManager:
    def check_existing_instances(self) -> List[ProcessInfo]
    def terminate_duplicates(self) -> bool
    def setup_preferred_autostart(self, method: str) -> bool
    def cleanup_conflicting_autostart(self) -> bool
```

### 2. Global Hotkey Manager Component

**Purpose**: Register and handle Ctrl+Alt hotkey activation

**Key Classes**:
- `HotkeyManager`: Main hotkey controller
- `KeyListener`: Background key monitoring
- `VoiceActivator`: Interface to voice system

**Interfaces**:
```python
class HotkeyManager:
    def register_hotkey(self, keys: List[str], callback: Callable) -> bool
    def unregister_hotkey(self, keys: List[str]) -> bool
    def start_listening(self) -> None
    def stop_listening(self) -> None
```

### 3. Enhanced Cursor Typing Component

**Purpose**: Improved text insertion with better window detection

**Key Classes**:
- `CursorTypingManager`: Main typing orchestrator
- `WindowDetector`: Active window and cursor detection
- `TextInjector`: Multiple injection methods

**Interfaces**:
```python
class CursorTypingManager:
    def type_at_cursor(self, text: str) -> TypingResult
    def detect_active_window(self) -> WindowInfo
    def get_injection_method(self) -> InjectionMethod
    def fallback_to_clipboard(self, text: str) -> bool
```

### 4. Enhanced Tray Application

**Purpose**: Unified tray interface with hotkey and service management

**Key Classes**:
- `VoxtralTrayUnified`: Single tray implementation
- `StatusManager`: Service status tracking
- `NotificationManager`: User feedback

## Data Models

### ProcessInfo
```python
@dataclass
class ProcessInfo:
    pid: int
    name: str
    cmdline: List[str]
    port: Optional[int]
    start_time: float
```

### WindowInfo
```python
@dataclass
class WindowInfo:
    window_id: str
    title: str
    class_name: str
    process_name: str
    is_text_editor: bool
    cursor_position: Optional[Tuple[int, int]]
```

### TypingResult
```python
@dataclass
class TypingResult:
    success: bool
    method_used: str
    characters_typed: int
    error_message: Optional[str]
    fallback_used: bool
```

### HotkeyConfig
```python
@dataclass
class HotkeyConfig:
    keys: List[str]
    enabled: bool
    feedback_type: str  # 'visual', 'audio', 'both', 'none'
    toggle_mode: bool   # True for toggle, False for push-to-talk
```

## Error Handling

### Service Conflicts
- **Detection**: Scan for existing processes on startup
- **Resolution**: Terminate older instances gracefully
- **Prevention**: Lock file mechanism to prevent new conflicts
- **Recovery**: Automatic restart with exponential backoff

### Hotkey Registration Failures
- **Detection**: Test hotkey registration on startup
- **Fallback**: Try alternative key combinations
- **User Notification**: Clear error messages about conflicts
- **Graceful Degradation**: Continue without hotkeys if necessary

### Cursor Typing Failures
- **Method Cascade**: Try direct typing → clipboard → notification
- **Window Detection**: Fallback to focused window if specific detection fails
- **User Feedback**: Clear indication of which method was used
- **Error Logging**: Detailed logs for troubleshooting

### Configuration Errors
- **Validation**: Check config values on load
- **Defaults**: Fallback to sensible defaults
- **User Notification**: Warn about invalid configurations
- **Auto-repair**: Fix common configuration issues automatically

## Testing Strategy

### Unit Tests
- **Service Manager**: Mock process detection and termination
- **Hotkey Manager**: Simulate key events and callbacks
- **Cursor Typing**: Mock window detection and text injection
- **Configuration**: Test config loading and validation

### Integration Tests
- **End-to-End Hotkey**: Test full hotkey → voice → typing flow
- **Service Startup**: Test various startup scenarios
- **Multi-Display**: Test on different desktop environments
- **Error Recovery**: Test failure scenarios and recovery

### System Tests
- **Real Environment**: Test on actual Debian 12 GNOME Wayland
- **Performance**: Measure hotkey response time and resource usage
- **Compatibility**: Test with various applications and text editors
- **Stress Testing**: Multiple rapid activations and edge cases

### Manual Testing Scenarios
1. **Duplicate Service Prevention**:
   - Enable both systemd and desktop autostart
   - Reboot system
   - Verify only one instance runs

2. **Hotkey Functionality**:
   - Press Ctrl+Alt in various applications
   - Test toggle vs push-to-talk modes
   - Verify visual/audio feedback

3. **Cursor Typing Accuracy**:
   - Test in text editors, browsers, terminals
   - Verify text appears at cursor position
   - Test fallback to clipboard method

4. **Error Recovery**:
   - Kill processes manually
   - Test automatic restart
   - Verify graceful degradation

## Implementation Phases

### Phase 1: Service Management (Priority: High)
- Implement duplicate detection and termination
- Create unified startup script
- Add configuration for preferred startup method
- Test on clean system installation

### Phase 2: Global Hotkey System (Priority: High)
- Integrate pynput for global key listening
- Add hotkey configuration to voxtral.yaml
- Implement toggle and push-to-talk modes
- Add visual/audio feedback options

### Phase 3: Enhanced Cursor Typing (Priority: Medium)
- Improve window detection algorithms
- Add application-specific typing strategies
- Implement better fallback mechanisms
- Add cursor position detection where possible

### Phase 4: Integration and Polish (Priority: Medium)
- Integrate all components into unified tray
- Add comprehensive error handling
- Implement user-friendly notifications
- Create configuration UI improvements

## Configuration Changes

### New Configuration Options
```yaml
# Service management
service:
  preferred_startup_method: "systemd"  # "systemd", "desktop", "manual"
  check_duplicates: true
  auto_restart: true
  restart_delay: 5

# Global hotkeys
hotkeys:
  activation_keys: ["ctrl", "alt"]
  enabled: true
  toggle_mode: true  # true = toggle, false = push-to-talk
  feedback:
    visual: true
    audio: false
    notification: true

# Enhanced cursor typing
cursor_typing:
  detection_method: "auto"  # "auto", "window_focus", "clipboard_only"
  fallback_to_clipboard: true
  typing_delay: 0.05
  window_detection_timeout: 2.0
  preferred_apps: ["code", "gedit", "kate", "sublime"]
```

## Security Considerations

### Hotkey Security
- **Key Logging Prevention**: Only register specific key combinations
- **Permission Checks**: Verify user has input device access
- **Isolation**: Hotkey handler runs in separate thread
- **Resource Limits**: Prevent hotkey spam attacks

### Process Management Security
- **Permission Validation**: Only terminate own processes
- **PID Validation**: Verify process ownership before termination
- **Safe Defaults**: Conservative process detection to avoid false positives
- **Audit Logging**: Log all process management actions

### Text Injection Security
- **Input Sanitization**: Validate text before injection
- **Application Whitelisting**: Optional restriction to specific apps
- **Clipboard Isolation**: Clear clipboard after use if configured
- **Permission Checks**: Verify accessibility permissions

## Performance Considerations

### Memory Usage
- **Hotkey Listener**: Minimal background thread (~1MB)
- **Service Manager**: On-demand activation only
- **Window Detection**: Cache window information
- **Configuration**: Lazy loading of config sections

### CPU Usage
- **Hotkey Detection**: Event-driven, not polling
- **Process Scanning**: Efficient process enumeration
- **Window Detection**: Optimized X11/Wayland queries
- **Background Tasks**: Use appropriate sleep intervals

### Startup Time
- **Parallel Initialization**: Start components concurrently
- **Lazy Loading**: Load heavy components on first use
- **Cache Warming**: Pre-load common window information
- **Error Handling**: Fast failure for unavailable features

## Compatibility Matrix

| Feature | GNOME Wayland | GNOME X11 | KDE Wayland | KDE X11 | XFCE |
|---------|---------------|-----------|-------------|---------|------|
| Service Management | ✅ | ✅ | ✅ | ✅ | ✅ |
| Global Hotkeys | ✅ | ✅ | ✅ | ✅ | ✅ |
| Direct Typing | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Clipboard Fallback | ✅ | ✅ | ✅ | ✅ | ✅ |
| Window Detection | ⚠️ | ✅ | ✅ | ✅ | ✅ |

**Legend**: ✅ Full Support, ⚠️ Limited Support, ❌ Not Supported