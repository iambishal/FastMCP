"""Enterprise Tools MCP Server - Main application entry point."""

import sys

from fastmcp import FastMCP
from tools.registry import register_tools
from utility.logging import setup_logging

from starlette.requests import Request
from starlette.responses import PlainTextResponse
from fastmcp.server.auth.providers.jwt import JWTVerifier


logger = setup_logging(__name__)


#authProvider = JWTVerifier(
#    jwks_uri="https://your-auth-system.com/.well-known/jwks.json",
#    issuer="https://your-auth-system.com", 
#    audience="your-mcp-server"
#)


# Create FastMCP instance
mcp = FastMCP(
    name="Indy-mcp-server",
#    auth=authProvider,
    version="1.0.0"
)

try:
    register_tools(mcp)
    logger.info("MCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MCP server: {e}", exc_info=True)
    raise


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

if __name__ == "__main__":
    # Run with HTTP transport on 0.0.0.0:8000
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )

