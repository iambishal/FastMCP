import requests

PETSTORE_BASE_URL = "https://petstore.swagger.io/v2"


def findPetsByStatus(status: str) -> dict:
    """
    Find pets by status from the Petstore API.
    :param status: Pet status to filter by. One of: available, pending, sold
    """
    valid_statuses = {"available", "pending", "sold"}
    if status not in valid_statuses:
        return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"}

    response = requests.get(
        f"{PETSTORE_BASE_URL}/pet/findByStatus",
        params={"status": status}
    )
    response.raise_for_status()
    return {"pets": response.json()}


def addClient(ClientBasicInformation):
    # Here you would implement the logic to add a client to your database
    # For demonstration purposes, we'll just return a success message
    return {
        "message": "Client added successfully",
        "client_info": {
            "basic_information": ClientBasicInformation.dict(),
        }
    }
def addClientAddress(ClientAddress):
    # Here you would implement the logic to add a client's address to your database
    # For demonstration purposes, we'll just return a success message
    return {
        "message": "Client address added successfully",
        "client_info": {
            "address": ClientAddress.dict(),
        }
    }
def addClientSuitability(ClientSuitability):
    # Here you would implement the logic to add a client's suitability information to your database
    # For demonstration purposes, we'll just return a success message
    return {
        "message": "Client suitability information added successfully",
        "client_info": {
            "suitability": ClientSuitability.dict(),
        }
    }
