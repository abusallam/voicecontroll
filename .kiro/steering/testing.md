# Testing Guidelines - Voxtral Voice Platform

## Testing Strategy (Established and Proven)

### Manual Testing Protocol ✅
This protocol was successfully used to validate the stable release:

#### Test 1: Quick Record (5s)
**Steps**:
1. Right-click microphone tray icon
2. Click "🎙️ Quick Record (5s)"
3. Speak clearly for 3-4 seconds
4. Wait for transcription and typing

**Expected Results**:
- No "cannot reshape tensor" errors
- Clean transcription without crashes
- Text appears at cursor position
- Typing method and timing displayed (e.g., "✅ Typed using ydotool_sudo (500ms)")

#### Test 2: Continuous Dictation
**Steps**:
1. Right-click microphone tray icon
2. Click "🎧 Start Continuous"
3. Speak, pause 2-3 seconds, speak again
4. Right-click and click "🔴 Stop Continuous"

**Expected Results**:
- Voice activity detection works (processes after pauses)
- Multiple speech segments transcribed correctly
- Stop function works immediately
- No buffer overflow errors

#### Test 3: Quit Function
**Steps**:
1. Right-click microphone tray icon
2. Click "❌ Quit"

**Expected Results**:
- Application quits immediately
- Tray icon disappears
- Process terminates completely
- Clean shutdown messages in terminal

#### Test 4: Test System
**Steps**:
1. Right-click microphone tray icon
2. Click "🧪 Test System"

**Expected Results**:
- Terminal window opens
- System status displayed
- All dependencies checked
- Performance metrics shown

#### Test 5: Services Menu
**Steps**:
1. Right-click microphone tray icon
2. Hover over "🔧 Services"
3. Click folder options (Agent, Tools, Scripts, Project Root)

**Expected Results**:
- File manager windows open
- Correct directories displayed
- All menu items responsive

### Automated Testing

#### System Test Script
```bash
# Run comprehensive system test
uv run scripts/test_system.py
```

**Checks**:
- Python environment and dependencies
- GTK libraries availability
- Audio system functionality
- Typing tools availability
- Whisper model loading
- Process management utilities

#### Process Management Test
```bash
# Test process cleanup
uv run scripts/kill_tray.py
ps aux | grep voxtral  # Should show no processes
```

### Performance Testing

#### Memory Usage Monitoring
```bash
# Monitor memory during operation
ps aux | grep voxtral_tray_stable
# Expected: ~1GB RSS memory usage
```

#### Typing Performance Testing
- Quick Record: Should complete in < 10 seconds total
- Typing latency: Should be < 1 second for most methods
- Fallback testing: Should gracefully fall back to clipboard if direct typing fails

### Error Condition Testing

#### Audio Error Scenarios
- Very short audio (< 1 second): Should skip processing
- Silent audio: Should detect and skip
- Invalid audio data: Should handle gracefully
- Microphone not available: Should show clear error

#### Process Conflict Testing
- Multiple tray instances: Should be prevented
- Hanging processes: Should be killable with kill_tray.py
- Service conflicts: Should detect and resolve

#### GTK Error Testing
- GTK not available: Should fail gracefully with clear message
- Tray system not available: Should show appropriate error
- Menu operations: Should handle exceptions without crashing

### Regression Testing Checklist

Before any code changes, verify:
- [ ] All 5 manual tests pass
- [ ] System test script passes
- [ ] No memory leaks during extended use
- [ ] Performance metrics within acceptable ranges
- [ ] Error handling works for all known failure modes

### Test Environment Setup

#### Required System State
```bash
# Clean environment
uv run scripts/kill_tray.py
ps aux | grep voxtral  # Should be empty

# Dependencies available
which ydotool wtype xdotool
dpkg -l | grep python3-gi

# Audio system working
arecord -d 2 test.wav && aplay test.wav && rm test.wav
```

#### Test Data
- Use consistent test phrases for transcription accuracy comparison
- Test with various audio conditions (quiet, loud, background noise)
- Test with different microphone setups

### Continuous Integration (Future)

#### Automated Test Pipeline
1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **System Tests**: Test full application functionality
4. **Performance Tests**: Verify performance requirements
5. **Security Tests**: Check for vulnerabilities

#### Test Reporting
- Test results should be logged and tracked
- Performance metrics should be monitored over time
- Regression detection should trigger alerts
- Test coverage should be maintained

### Known Test Limitations

#### Manual Testing Required
- Audio quality assessment requires human evaluation
- User interface responsiveness needs manual verification
- Real-world usage scenarios require human testing

#### Environment Dependencies
- Tests require specific Linux desktop environment
- Audio hardware availability affects test results
- Network connectivity may affect some tests

### Test Documentation

#### Test Results Recording
- Document test outcomes with timestamps
- Record performance metrics for comparison
- Note any deviations from expected behavior
- Track test environment details

#### Issue Tracking
- Link test failures to specific issues
- Document reproduction steps for failures
- Track resolution status and verification
- Maintain test case updates based on fixes