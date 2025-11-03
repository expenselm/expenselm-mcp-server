# [ExpenseLM](https://expenselm.ai) MCP Server

## Introduction

MCP server for [ExpenseLM](https://expenselm.ai).

## Installation

### Prerequisites

* uv
* Python 3.9+
* ExpenseLM API key ([Instructions](https://www.expenselm.ai/docs/mcp-server-guide))

## Setup MCP Client

### Claude Desktop (Mac)

Add the following MCP server in your Claude Desktop configuration.

Config file (create if not exists): ~/Library/Application Support/Claude/claude_desktop_config.json

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

### Claude Desktop (Windows)

Add the following MCP server in your Claude Desktop configuration.

Config file (create if not exists): %AppData%\Claude\claude_desktop_config.json (e.g. C:\Users\[YourUsername]\AppData\Roaming\Claude\claude_desktop_config.json)

Add the following into your config file.

```json
{
  "mcpServers": {
    "expenselm": {
      "command": "uv",
      "args": [
        "tool",
        "run",
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
