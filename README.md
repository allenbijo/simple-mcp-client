# MCP Client

## Overview
This MCP (Model Context Protocol) Client is a command-line tool that allows MCP Servers to interact with both OpenAI's GPT and Anthropic's Claude models. It provides a simple interface for users to send queries and receive responses from either AI model.

## Features
- Supports both GPT and Anthropic models
- Command-line interface for easy interaction
- Configuration via `mcp_config.json`
- Runs using `uv` for efficient execution

## Requirements
- Python 3.8+
- `uv` (for running the script)
- OpenAI and Anthropic API keys

## Installation
1. Clone the repository:
   ```sh
   git clone <your-repo-url>
   cd mcp-client
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up the `mcp_config.json` file:
   ```json
    {
        "mcpServers": {
            "server1": {
                "command": "uv",
                "args": [
                    "--directory",
                    "<path to server 1>",
                    "run",
                    "main.py"
                ]
            },
            "sysinfo2": {
                "command": "uv",
                "args": [
                    "--directory",
                    "<path to server 2>",
                    "run",
                    "main.py"
                ]
            }
        }
    }
   ```
4. Set up the environment file `(.env)`
   ```sh
   API_KEY=<Enter API key>
   ```

## Usage
To start the MCP client, run:
```sh
uv run main.py
```
This will initialize the chat client and allow you to interact with the selected AI model.

## Configuration
Modify the `mcp_config.json` to add or remove servers. Modify the `.env` to add API Keys.

## License
This project is licensed under the MIT License.

## Contributions
Feel free to open issues or submit pull requests to enhance functionality!

