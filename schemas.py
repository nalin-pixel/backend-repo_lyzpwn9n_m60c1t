"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal

# Core salon models

class Service(BaseModel):
    """
    Storitev v salonu
    Collection: "service"
    """
    key: Literal["striženje", "barvanje"] = Field(..., description="Tip storitve")
    title: str = Field(..., description="Prijazno ime storitve za prikaz")
    min_duration: int = Field(..., ge=15, le=480, description="Minimalno trajanje v minutah")
    max_duration: int = Field(..., ge=15, le=480, description="Maksimalno trajanje v minutah")
    step: int = Field(30, ge=5, le=120, description="Korak izbire trajanja v minutah")
    price_from: Optional[float] = Field(None, ge=0, description="Cena od (opcijsko)")

class Appointment(BaseModel):
    """
    Termin naročila
    Collection: "appointment"
    """
    service: Literal["striženje", "barvanje"] = Field(..., description="Storitev")
    duration_minutes: int = Field(..., ge=15, le=480, description="Trajanje v minutah")
    date: str = Field(..., description="Datum v obliki YYYY-MM-DD")
    start_time: str = Field(..., description="Začetek HH:MM (24h)")
    end_time: Optional[str] = Field(None, description="Konec HH:MM (24h) – izračuna backend")
    name: str = Field(..., description="Ime in priimek")
    phone: str = Field(..., description="Telefon")
    email: Optional[EmailStr] = Field(None, description="E-pošta (opcijsko)")
    notes: Optional[str] = Field(None, description="Opombe")
    status: Literal["potrjeno", "preklicano", "v_procesu"] = Field("potrjeno", description="Stanje termina")

# Example schemas kept for reference (unused by this app)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
