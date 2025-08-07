# Test on Save Hook

## Trigger
- **Event**: File save
- **Pattern**: `scripts/voxtral_tray_*.py`
- **Description**: Automatically run system tests when tray application files are modified

## Actions
1. Kill any running tray processes
2. Run comprehensive system test
3. Check for common issues (GTK availability, audio dependencies)
4. Report test results

## Implementation
```bash
# Kill existing processes
uv run scripts/kill_tray.py

# Run system test
uv run scripts/test_system.py

# Check for process conflicts
ps aux | grep voxtral
```

## Benefits
- Immediate feedback on code changes
- Prevents deployment of broken tray applications
- Ensures system dependencies are met
- Catches process management issues early