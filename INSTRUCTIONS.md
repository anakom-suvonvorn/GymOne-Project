# Gym Management API — Setup & Testing Instructions

## Prerequisites
- Docker Desktop installed and running
- Node.js installed (for `npx`)

## Step 1 — Pull the Docker Image

```bash
docker pull anakom978/gym-api-mcp
```

## Step 2 — Run the Server

```bash
docker run -p 8000:8000 anakom978/gym-api-mcp
```

Leave this terminal open. The server is ready when you see:
```
Uvicorn running on http://0.0.0.0:8000
```

## Step 3 — Connect to Claude Desktop

1. Find your Claude Desktop config file : `claude_desktop_config.json`

2. Add this to the file:
```json
{
  "mcpServers": {
    "gym-api": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://127.0.0.1:8000/mcp"
      ]
    }
  }
}
```

3. Make sure the Docker container from Step 2 is still running

4. Restart Claude Desktop — the gym API tools will appear automatically

## Stopping the Server

Press `Ctrl+C` in the terminal running the container, or run:
```bash
docker stop $(docker ps -q --filter ancestor=anakom978/gym-api-mcp)
```
