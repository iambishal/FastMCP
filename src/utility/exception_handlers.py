"""Exception handlers for the application."""

from starlette.requests import Request
from starlette.responses import JSONResponse


def register_exception_handlers(app, settings, logger):
    """
    Register all exception handlers for the application.
    
    Args:
        app: Starlette app instance
        settings: Application settings
        logger: Logger instance
    """
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Handle all uncaught exceptions.
        
        Args:
            request: The request object
            exc: The exception that was raised
            
        Returns:
            JSONResponse: Error response with status 500
        """
        request_id = getattr(request.state, 'request_id', 'N/A')
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={'request_id': request_id}
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "message": str(exc)
            }
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """
        Handle 404 Not Found errors.
        
        Args:
            request: The request object
            exc: The 404 exception
            
        Returns:
            JSONResponse: Error response with status 404
        """
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "path": str(request.url.path),
                "message": "The requested resource was not found"
            }
        )
    
    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc):
        """
        Handle 405 Method Not Allowed errors.
        
        Args:
            request: The request object
            exc: The 405 exception
            
        Returns:
            JSONResponse: Error response with status 405
        """
        return JSONResponse(
            status_code=405,
            content={
                "error": "Method not allowed",
                "path": str(request.url.path),
                "method": request.method,
                "message": f"The {request.method} method is not allowed for this resource"
            }
        )
    
    @app.exception_handler(422)
    async def validation_error_handler(request: Request, exc):
        """
        Handle 422 Validation Error responses.
        
        Args:
            request: The request object
            exc: The validation exception
            
        Returns:
            JSONResponse: Error response with status 422
        """
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "path": str(request.url.path),
                "message": "Request validation failed"
            }
        )
