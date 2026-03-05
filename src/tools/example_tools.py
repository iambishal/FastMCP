"""Petstore API example tools."""

import httpx
from pydantic import BaseModel, Field


class PetStatusInput(BaseModel):
    """Schema for pet status input with validation."""

    status: str = Field(
        ..., 
        pattern=r'^(available|pending|sold)$',
        description="Pet status: available, pending, or sold"
    )


async def findPetsByStatus(
    status: str,
    http_client,
    logger=None
) -> dict:
    """
    Find pets by status from Petstore API with resilience patterns.
    
    Args:
        status: Pet status (available, pending, sold)
        http_client: HTTP client manager instance
        logger: Optional logger instance
        
    Returns:
        dict: Response with pets list
        
    Raises:
        httpx.HTTPError: If API request fails after retries
    """
    valid_statuses = {"available", "pending", "sold"}
    if status not in valid_statuses:
        error_msg = f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
        if logger:
            logger.warning(error_msg)
        return {"error": error_msg}
    
    try:
        pets = await http_client.get(
            "/pet/findByStatus",
            params={"status": status}
        )
        
        if logger:
            logger.info(
                f"Successfully retrieved {len(pets)} pets with status: {status}",
                extra={'status': status, 'count': len(pets)}
            )
        
        return {"pets": pets, "count": len(pets), "status": status}
        
    except httpx.HTTPStatusError as e:
        error_msg = f"API returned error {e.response.status_code}: {e.response.text}"
        if logger:
            logger.error(error_msg, extra={'status_code': e.response.status_code})
        return {"error": error_msg, "status_code": e.response.status_code}
        
    except httpx.TimeoutException:
        error_msg = "Request timeout while fetching pets"
        if logger:
            logger.error(error_msg)
        return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error fetching pets: {str(e)}"
        if logger:
            logger.error(error_msg, exc_info=True)
        return {"error": error_msg}
