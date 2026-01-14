from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    expiresAt: datetime
    username: str
    role: str

class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    price: float

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float

    class Config:
        from_attributes = True
