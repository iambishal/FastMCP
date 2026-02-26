# -----------------------------
# INPUT SCHEMAS
# -----------------------------

from pydantic import BaseModel, Field


class ClientBasicInformation(BaseModel):
    name: str = Field(..., description="Client's name")
    email: str = Field(..., description="Client's email address")
    date_of_birth: str = Field(..., description="Client's date of birth (YYYY-MM-DD)")
    

class  ClientAddress(BaseModel):
    street: str = Field(..., description="Client's street address")
    city: str = Field(..., description="Client's city")
    state: str = Field(..., description="Client's state")
    zip_code: str = Field(..., description="Client's ZIP code")

class ClientSuitability(BaseModel):
    investment_experience: str = Field(..., description="Client's investment experience")
    risk_tolerance: str = Field(..., description="Client's risk tolerance level")
    investment_objectives: str = Field(..., description="Client's investment objectives")
    annual_income: float = Field(..., description="Client's annual income")
    net_worth: float = Field(..., description="Client's net worth")

class PetStatusInput(BaseModel):
    status: str = Field(..., description="Pet status to filter by. One of: available, pending, sold")
