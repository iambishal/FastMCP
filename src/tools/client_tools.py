"""Client tools module for managing client operations."""

import requests
from pydantic import BaseModel, Field
from src.utility.logging import setup_logging

logger = setup_logging(__name__)

PETSTORE_BASE_URL = "https://petstore.swagger.io/v2"


class ClientBasicInformation(BaseModel):
    """Schema for basic client information."""

    name: str = Field(..., description="Client's name")
    email: str = Field(..., description="Client's email address")
    date_of_birth: str = Field(..., description="Client's date of birth (YYYY-MM-DD)")


class ClientAddress(BaseModel):
    """Schema for client address information."""

    street: str = Field(..., description="Client's street address")
    city: str = Field(..., description="Client's city")
    state: str = Field(..., description="Client's state")
    zip_code: str = Field(..., description="Client's ZIP code")


class ClientSuitability(BaseModel):
    """Schema for client suitability information."""

    investment_experience: str = Field(..., description="Client's investment experience")
    risk_tolerance: str = Field(..., description="Client's risk tolerance level")
    investment_objectives: str = Field(..., description="Client's investment objectives")
    annual_income: float = Field(..., description="Client's annual income")
    net_worth: float = Field(..., description="Client's net worth")


class PetStatusInput(BaseModel):
    """Schema for pet status input."""

    status: str = Field(..., description="Pet status to filter by. One of: available, pending, sold")


def findPetsByStatus(status: str) -> dict:
    """
    Find pets by status from the Petstore API.
    
    Args:
        status: Pet status to filter by. One of: available, pending, sold
        
    Returns:
        dict: Response containing pets list or error message
        
    Raises:
        requests.HTTPError: If the API request fails
    """
    valid_statuses = {"available", "pending", "sold"}
    if status not in valid_statuses:
        return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"}

    try:
        response = requests.get(
            f"{PETSTORE_BASE_URL}/pet/findByStatus",
            params={"status": status}
        )
        response.raise_for_status()
        logger.info(f"Successfully retrieved pets with status: {status}")
        return {"pets": response.json()}
    except requests.RequestException as e:
        logger.error(f"Error fetching pets by status: {e}")
        raise


def addClient(client_info: ClientBasicInformation) -> dict:
    """
    Add a new client to the system.
    
    Args:
        client_info: Client basic information object
        
    Returns:
        dict: Success message with client information
    """
    try:
        result = {
            "message": "Client added successfully",
            "client_info": {
                "basic_information": client_info.dict(),
            }
        }
        logger.info(f"Client added successfully: {client_info.email}")
        return result
    except Exception as e:
        logger.error(f"Error adding client: {e}")
        raise


def addClientAddress(client_address: ClientAddress) -> dict:
    """
    Add a new client's address to the system.
    
    Args:
        client_address: Client address object
        
    Returns:
        dict: Success message with address information
    """
    try:
        result = {
            "message": "Client address added successfully",
            "client_info": {
                "address": client_address.dict(),
            }
        }
        logger.info(f"Client address added successfully: {client_address.zip_code}")
        return result
    except Exception as e:
        logger.error(f"Error adding client address: {e}")
        raise


def addClientSuitability(client_suitability: ClientSuitability) -> dict:
    """
    Add a client's suitability information to the system.
    
    Args:
        client_suitability: Client suitability object
        
    Returns:
        dict: Success message with suitability information
    """
    try:
        result = {
            "message": "Client suitability information added successfully",
            "client_info": {
                "suitability": client_suitability.dict(),
            }
        }
        logger.info("Client suitability information added successfully")
        return result
    except Exception as e:
        logger.error(f"Error adding client suitability: {e}")
        raise
