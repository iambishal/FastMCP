"""Tool registry with Petstore API support using dependency injection."""

from fastmcp import FastMCP
from tools.example_tools import (
    findPetsByStatus,
    PetStatusInput,
)
from container import Container


# Tool metadata
TOOL_METADATA = {
    "find_pets_by_status": {
        "name": "find_pets_by_status",
        "description": "Find pets from Petstore API filtered by status (available, pending, or sold)",
        "tags": ["External API", "Pets"],
        "timeout": 30,
    },
}


def register_tools(
    mcp: FastMCP,
    container: Container
) -> None:
    """
    Register all MCP tools with proper error handling and logging.
    
    Uses dependency injection to obtain required dependencies from the container.
    
    Args:
        mcp: FastMCP instance to register tools with
        container: Dependency injection container
        
    Raises:
        Exception: If tool registration fails
    """
    # Get dependencies from container (call providers)
    api_manager = container.api_manager()
    logger = container.logger()
    
    try:
        @mcp.tool(
            name=TOOL_METADATA["find_pets_by_status"]["name"],
            description=TOOL_METADATA["find_pets_by_status"]["description"],
            tags=TOOL_METADATA["find_pets_by_status"]["tags"],
            timeout=TOOL_METADATA["find_pets_by_status"]["timeout"]
        )
        async def find_pets_by_status_tool(pet_status: PetStatusInput) -> dict:
            """
            Find pets by status from the Petstore API.
            
            Args:
                pet_status: Pet status filter (available, pending, sold)
                
            Returns:
                dict: Response with pets list or error
            """
            try:
                # Get the Petstore API client from the API manager
                petstore_client = api_manager.get("petstore")
                return await findPetsByStatus(pet_status.status, petstore_client, logger)
            except Exception as e:
                logger.error(f"Error in find_pets_by_status: {e}", exc_info=True)
                return {"error": "Failed to fetch pets", "details": str(e)}
        
        logger.info(f"Successfully registered {len(TOOL_METADATA)} tools")
    
    except Exception as e:
        logger.error(f"Critical error during tool registration: {e}", exc_info=True)
        raise
