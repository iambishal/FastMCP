"""Tool registry module for registering MCP tools."""

from fastmcp import FastMCP
from src.tools.client_tools import (
    addClient,
    addClientAddress,
    addClientSuitability,
    findPetsByStatus,
    ClientBasicInformation,
    ClientAddress,
    ClientSuitability,
    PetStatusInput
)
from src.utility.logging import setup_logging

logger = setup_logging(__name__)

# Tool Constants
TOOL_NAMES = {
    "add_client": "add_client",
    "add_client_address": "add_client_address",
    "add_client_suitability": "add_client_suitability",
    "find_pets_by_status": "find_pets_by_status",
}

TOOL_DESCRIPTIONS = {
    "add_client": "Add a new client to the system",
    "add_client_address": "Add a new client address to the system",
    "add_client_suitability": "Add a new client suitability to the system",
    "find_pets_by_status": "Find pets from the Petstore API by status (available, pending, sold)",
}


def register_tools(mcp: FastMCP) -> None:
    """
    Register all available tools with the FastMCP instance.
    
    Args:
        mcp: FastMCP instance to register tools with
        
    Raises:
        Exception: If tool registration fails
    """
    try:
        @mcp.tool(
            name=TOOL_NAMES["add_client"],
            description=TOOL_DESCRIPTIONS["add_client"]
        )
        def add_client(client_info: ClientBasicInformation) -> dict:
            """Add a new client to the system."""
            return addClient(client_info)

        @mcp.tool(
            name=TOOL_NAMES["add_client_address"],
            description=TOOL_DESCRIPTIONS["add_client_address"]
        )
        def add_client_address(client_address: ClientAddress) -> dict:
            """Add a new client address to the system."""
            return addClientAddress(client_address)

        @mcp.tool(
            name=TOOL_NAMES["add_client_suitability"],
            description=TOOL_DESCRIPTIONS["add_client_suitability"]
        )
        def add_client_suitability(client_suitability: ClientSuitability) -> dict:
            """Add a new client suitability to the system."""
            return addClientSuitability(client_suitability)

        @mcp.tool(
            name=TOOL_NAMES["find_pets_by_status"],
            description=TOOL_DESCRIPTIONS["find_pets_by_status"]
        )
        def find_pets_by_status(pet_status: PetStatusInput) -> dict:
            """Find pets from the Petstore API by status."""
            return findPetsByStatus(pet_status.status)
        
        logger.info("Successfully registered all tools")
    
    except Exception as e:
        logger.error(f"Error registering tools: {e}", exc_info=True)
        raise
