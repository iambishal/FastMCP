from fastmcp import FastMCP
from src.registry import register_tools

# Create FastMCP instance
mcp = FastMCP(
    name="enterprise-tools-mcp",
    version="1.0.0"
)

register_tools(mcp)

# Expose for HTTP serving
app = mcp.http_app()