from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import crud
from app.schemas import WineCreate, WineResponse, WineUpdate, CellarStats

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Wine Cellar Manager",
    description="Manage your personal wine collection.",
    version="1.0.0",
)


@app.get("/wines", response_model=list[WineResponse], summary="List wines")
def list_wines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    wine_type: Optional[str] = Query(None, description="Filter by type (red, white, rosé, sparkling, dessert, other)"),
    country: Optional[str] = Query(None, description="Filter by country"),
    min_vintage: Optional[int] = Query(None, ge=1800, le=2100),
    max_vintage: Optional[int] = Query(None, ge=1800, le=2100),
    min_rating: Optional[float] = Query(None, ge=0.0, le=100.0),
    search: Optional[str] = Query(None, description="Search by name, winery, region, or grape variety"),
    db: Session = Depends(get_db),
):
    return crud.get_wines(
        db,
        skip=skip,
        limit=limit,
        wine_type=wine_type,
        country=country,
        min_vintage=min_vintage,
        max_vintage=max_vintage,
        min_rating=min_rating,
        search=search,
    )


@app.post("/wines", response_model=WineResponse, status_code=201, summary="Add a wine")
def add_wine(wine: WineCreate, db: Session = Depends(get_db)):
    return crud.create_wine(db, wine)


@app.get("/wines/{wine_id}", response_model=WineResponse, summary="Get a wine by ID")
def get_wine(wine_id: int, db: Session = Depends(get_db)):
    db_wine = crud.get_wine(db, wine_id)
    if db_wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return db_wine


@app.patch("/wines/{wine_id}", response_model=WineResponse, summary="Update a wine")
def update_wine(wine_id: int, wine: WineUpdate, db: Session = Depends(get_db)):
    db_wine = crud.update_wine(db, wine_id, wine)
    if db_wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return db_wine


@app.delete("/wines/{wine_id}", response_model=WineResponse, summary="Remove a wine")
def delete_wine(wine_id: int, db: Session = Depends(get_db)):
    db_wine = crud.delete_wine(db, wine_id)
    if db_wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return db_wine


@app.get("/stats", response_model=CellarStats, summary="Get cellar statistics")
def cellar_stats(db: Session = Depends(get_db)):
    return crud.get_cellar_stats(db)
