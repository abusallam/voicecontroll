# Security Check Hook

## Trigger
- **Event**: Pre-commit
- **Pattern**: All Python files
- **Description**: Scan for potential security issues before committing

## Actions
1. Check for hardcoded credentials or API keys
2. Verify no sensitive paths are exposed
3. Ensure proper input validation
4. Check for unsafe subprocess calls

## Implementation
```bash
# Check for potential secrets
grep -r "api_key\|password\|secret\|token" --include="*.py" .

# Check for hardcoded paths
grep -r "/home/\|/Users/" --include="*.py" .

# Check for unsafe subprocess calls
grep -r "subprocess.*shell=True" --include="*.py" .

# Check for eval/exec usage
grep -r "eval\|exec" --include="*.py" .
```

## Benefits
- Prevents accidental credential leaks
- Ensures secure coding practices
- Catches potential injection vulnerabilities
- Maintains clean public repository