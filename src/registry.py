from fastmcp import FastMCP
from src.tools.client_tools import addClient, addClientAddress, addClientSuitability, findPetsByStatus
from src.schema.client_schema import ClientBasicInformation, ClientAddress, ClientSuitability, PetStatusInput


def register_tools(mcp: FastMCP):

    @mcp.tool(
        name="add_client",
        description="Add a new client to the system"
    )
    def add_client(client_info: ClientBasicInformation):
        return addClient(client_info)

    @mcp.tool(
        name="add_client_address",
        description="Add a new client address to the system"
    )
    def add_client_address(client_address: ClientAddress):
        return addClientAddress(client_address)

    @mcp.tool(
        name="add_client_suitability",
        description="Add a new client suitability to the system"
    )
    def add_client_suitability(client_suitability: ClientSuitability):
        return addClientSuitability(client_suitability)

    @mcp.tool(
        name="find_pets_by_status",
        description="Find pets from the Petstore API by status (available, pending, sold)"
    )
    def find_pets_by_status(pet_status: PetStatusInput):
        return findPetsByStatus(pet_status.status)
