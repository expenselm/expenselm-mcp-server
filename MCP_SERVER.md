# ExpenseLM - MCP Server instructions

## Submit ExpenseLM MCP Server to public registries

### Offical Registry (https://github.com/modelcontextprotocol/registry)

* Update server.json version number
* Login mcp-publisher to Github

```bash
mcp-publisher login github
```

* Publish to MCP registry

```bash
mcp-publisher publish
```

* Verify package

```bash
curl "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.clarenceh/expenselm-mcp-server" | jq
```
