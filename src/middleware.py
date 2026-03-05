"""Enhanced middleware for request tracking, metrics, and resilience."""

import time
import uuid
import logging
from typing import Callable
from collections import defaultdict
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

logger = logging.getLogger("mcp.middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context (correlation ID, request ID)."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request context to all requests."""
        # Generate unique IDs for request tracking
        request_id = str(uuid.uuid4())
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        
        # Store in request state
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # Add to logging context
        logger = logging.LoggerAdapter(
            logging.getLogger("mcp"),
            {'request_id': request_id, 'correlation_id': correlation_id}
        )
        request.state.logger = logger
        
        response = await call_next(request)
        
        # Add tracking headers to response
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response



class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle uncaught exceptions gracefully."""
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, 'request_id', 'N/A')
            logger.error(
                f"Unhandled exception: {e}",
                exc_info=True,
                extra={'request_id': request_id}
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "message": "An unexpected error occurred. Please try again later."
                }
            )


def configure_middleware(app, settings):
    """
    Configure all middleware for the application.
    
    Args:
        app: FastAPI/Starlette application
        settings: Application settings
    """
    # CORS middleware (add first to handle preflight requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Error handling (should be early in chain)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Request context tracking
    app.add_middleware(RequestContextMiddleware)
 
    logger.info("All middleware configured successfully")
