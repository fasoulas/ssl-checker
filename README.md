# How to run
All actions below to be taken from the root folder

## As an MCP Server (locally)
1. Load environment: **source ./.venv/bin/activate**
2. Run server: **uvicorn check_ssl_mcp.main:app**

## As an MCP server in a Docker comtainer
1. Build image: **docker build --tag ssl-mcp-server:latest .**
2. Run image : **docker run -p 8000:8000 -e MCP_SERVER_TOKEN=XXX ssl-mcp-server:latest**

## As a command line tool (locally)
1.  Load environment: **source ./.venv/bin/activate**
2. Execute command **python ./check-ssl-mcp/main.py** https://cern.ch https://learn.heatgeek.com (pass a list of https urls)

