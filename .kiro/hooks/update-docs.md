# Update Documentation Hook

## Trigger
- **Event**: File save
- **Pattern**: `scripts/voxtral_tray_stable.py`, `tools/enhanced_cursor_typing.py`
- **Description**: Automatically update documentation when core files change

## Actions
1. Update feature list in README.md if new features detected
2. Update performance metrics if timing code changes
3. Update troubleshooting section if error handling changes
4. Regenerate API documentation for tools

## Implementation
```bash
# Check for new features in tray application
grep -n "def.*(" scripts/voxtral_tray_stable.py

# Update README performance section if timing changes
grep -n "time\|performance\|ms\|seconds" scripts/voxtral_tray_stable.py

# Update troubleshooting if error patterns change
grep -n "except\|error\|failed" scripts/voxtral_tray_stable.py
```

## Benefits
- Keeps documentation synchronized with code
- Prevents outdated feature descriptions
- Maintains accurate troubleshooting guides
- Ensures performance metrics stay current