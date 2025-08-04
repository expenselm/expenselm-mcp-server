# ExpenseLM MCP Server

## Introduction

MCP server for ExpenseLM.

## Installation

### Prerequisites

* uv

## Setup MCP Client

### Claude Desktop

Add the following MCP server in your Claude Desktop configuration.

For Mac: ~/Library/Application Support/Claude/claude_desktop_config.json

Add the following into your config file.

```json
{
  "mcpServers": {
    "expenselm": {
      "command": "uvx",
      "args": [
        "expenselm-mcp-server"
      ],
      "env": {
        "EXPENSELM_API_KEY": "Your ExpenseLM API Key",
        "MCP_TIMEOUT": "200000"
      }
    }
  }
}
```
