from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


WineType = Literal["red", "white", "rosé", "sparkling", "dessert", "other"]


class WineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    winery: str = Field(..., min_length=1, max_length=255)
    vintage: Optional[int] = Field(None, ge=1800, le=2100)
    wine_type: WineType
    region: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    grape_variety: Optional[str] = Field(None, max_length=255)
    quantity: int = Field(1, ge=0)
    rating: Optional[float] = Field(None, ge=0.0, le=100.0)
    price: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None

    @field_validator("wine_type", mode="before")
    @classmethod
    def normalize_wine_type(cls, v: str) -> str:
        return v.lower().strip()


class WineCreate(WineBase):
    pass


class WineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    winery: Optional[str] = Field(None, min_length=1, max_length=255)
    vintage: Optional[int] = Field(None, ge=1800, le=2100)
    wine_type: Optional[WineType] = None
    region: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    grape_variety: Optional[str] = Field(None, max_length=255)
    quantity: Optional[int] = Field(None, ge=0)
    rating: Optional[float] = Field(None, ge=0.0, le=100.0)
    price: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None

    @field_validator("wine_type", mode="before")
    @classmethod
    def normalize_wine_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.lower().strip()


class WineResponse(WineBase):
    id: int

    model_config = {"from_attributes": True}


class CellarStats(BaseModel):
    total_wines: int
    total_bottles: int
    average_rating: Optional[float]
    wines_by_type: dict[str, int]
