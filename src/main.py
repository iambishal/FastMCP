import sys

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Import configuration and utilities
from config import settings
from container import get_container

from middleware import configure_middleware
from tools.registry import register_tools
from utility.exception_handlers import register_exception_handlers

# Initialize dependency container
container = get_container()
logger = container.logger()

# Create FastMCP instance with enhanced configuration
mcp = FastMCP(
    name=settings.app_name,
    version=settings.app_version,
    # Uncomment and configure when enabling authentication
    # auth=JWTVerifier(
    #     jwks_uri=settings.jwt_jwks_uri,
    #     issuer=settings.jwt_issuer,
    #     audience=settings.jwt_audience
    # ) if settings.enable_auth else None,
)

# Initialize API Manager synchronously
try:
    api_manager = container.api_manager()
    api_manager.initialize_sync()
    logger.info("API Manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize API Manager: {e}", exc_info=True)
    sys.exit(1)

# Register tools
try:
    register_tools(mcp, container)
    logger.info("All tools registered successfully")
except Exception as e:
    logger.error(f"Failed to register tools: {e}", exc_info=True)
    sys.exit(1)

# Register Prompts

# Register Resources

# Register exception handlers
try:
    register_exception_handlers(mcp.http_app(), settings, logger)
    logger.info("Exception handlers registered successfully")
except Exception as e:
    logger.error(f"Failed to register exception handlers: {e}", exc_info=True)
    sys.exit(1)


# Configure middleware
try:
    configure_middleware(mcp.http_app(), settings)
    logger.info("Middleware configured successfully")
except Exception as e:
    logger.error(f"Failed to configure middleware: {e}", exc_info=True)
    sys.exit(1)


# Health check endpoints
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """
    Basic health check endpoint.
    
    Returns:
        JSONResponse: Health status
    """
    return JSONResponse({
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    })

if __name__ == "__main__":
    try:
        logger.info(f"Starting server on {settings.host}:{settings.port}")
        
        # Run with enhanced configuration
        mcp.run(
            transport="http",
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower()
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)
