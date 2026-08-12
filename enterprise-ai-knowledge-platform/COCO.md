# Enterprise AI Knowledge Platform

## Project Conventions

### Python
- Python 3.10+ with type hints on all public functions
- Pydantic v2 for data validation and serialization
- Ruff for linting and formatting (line length: 100)
- pytest for testing with markers: @unit, @integration, @e2e

### SQL Naming
- Tables: UPPER_SNAKE_CASE (e.g., DOCUMENT_REGISTRY)
- Columns: UPPER_SNAKE_CASE (e.g., DOCUMENT_ID)
- Stages: DEPARTMENT_DOCS (e.g., FINANCE_DOCS)
- Roles: CORTEX_AI_{DEPARTMENT} or CORTEX_AI_{FUNCTION}
- Warehouses: CORTEX_AI_{WORKLOAD}_WH

### Module Structure
Each module follows:
```
src/{module}/
    __init__.py          # Public API exports
    service.py           # Main service class
    models.py            # Module-specific models (if needed beyond shared)
    sql/                 # Embedded SQL templates (optional)
```

### Configuration
- All behavior is config-driven via YAML files in /config
- Environment overrides in /config/environments/{env}.yaml
- Secrets via environment variables with ${VAR} syntax in YAML

### Error Handling
- All exceptions inherit from PlatformError in src/shared/exceptions
- Errors include error_code for machine-readable classification
- Never swallow exceptions silently; log and re-raise or wrap

### Snowflake Session Management
- Use Snowpark Session via context manager
- One session per operation/request, not long-lived
- Always specify warehouse and role explicitly

### Testing
- Unit tests mock Snowflake session (no real connection)
- Integration tests use a dedicated test database
- All tests run in CI via GitHub Actions
