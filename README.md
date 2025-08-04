# ExpenseLM MCP Server

## Introduction

MCP server for ExpenseLM.

## Installation

### Prerequisites

* git
* Python
* uv

### Clone the source code to your local machine

```bash
git clone https://github.com/expenselm/expenselm-mcp-server.git
```

## Setup MCP Client

### Claude Desktop

Add the following MCP server in your Claude Desktop configuration.

For Mac: ~/Library/Application Support/Claude/claude_desktop_config.json

Add the following into your config file.

```json
{
  "mcpServers": {
    "expenselm": {
      "command": "uv",
      "args": [
        "run",
        "--with", "fastmcp",
        "--with", "httpx", 
        "fastmcp",
        "run",
        "~/workspace/expenselm/expenselm-mcp-server/expenselm_mcp_server.py"
      ],
      "env": {
        "EXPENSELM_API_KEY": "Your ExpenseLM API Key",
        "MCP_TIMEOUT": "200000"
      }
    }
  }
}
```
