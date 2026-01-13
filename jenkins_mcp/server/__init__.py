from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
import importlib
import os

# Disable DNS rebinding protection for Docker container networking
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False
)

# Configure uvicorn to bind to 0.0.0.0 for container networking
os.environ.setdefault('UVICORN_HOST', '0.0.0.0')
os.environ.setdefault('UVICORN_PORT', '8000')

# Create MCP server with security settings
mcp = FastMCP('rhoai-jenkins', transport_security=transport_security)

# Import all tool definitions for the unified Jenkins MCP server
print("Importing Jenkins tools")
importlib.import_module("jenkins_mcp.server.basic_tools")
importlib.import_module("jenkins_mcp.server.rhoai_tools")
importlib.import_module("jenkins_mcp.server.analysis_tools")
