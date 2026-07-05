from sqlalchemy import Column, Integer, String, Float, Text
from app.database import Base


class Wine(Base):
    __tablename__ = "wines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    winery = Column(String(255), nullable=False)
    vintage = Column(Integer, nullable=True)
    wine_type = Column(String(50), nullable=False)  # red, white, rosé, sparkling, dessert
    region = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    grape_variety = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    rating = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
