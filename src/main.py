"""Enterprise Tools MCP Server - Main application entry point."""

from fastmcp import FastMCP
from src.tools.registry import register_tools
from src.utility.logging import setup_logging

logger = setup_logging(__name__)

# Create FastMCP instance
mcp = FastMCP(
    name="enterprise-tools-mcp",
    version="1.0.0"
)

try:
    register_tools(mcp)
    logger.info("MCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MCP server: {e}", exc_info=True)
    raise

# Expose for HTTP serving
app = mcp.http_app()

if __name__ == "__main__":
    logger.info("Starting enterprise-tools-mcp server")