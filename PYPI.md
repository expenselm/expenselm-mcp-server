# ExpenseLM MCP Server - PyPI instructions

## Build package for publishing

```bash
uv build
```

## Publish to PyPI

Update the version (e.g. 0.2.0 to 0.2.1) in the following files:

* pyproject.toml
* src/expenselm_mcp_server/__init__.py

```bash
uv publish --token pypi-...

# where pypi- is your PyPI API token
```
