from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Wine
from app.schemas import WineCreate, WineUpdate, CellarStats


def get_wine(db: Session, wine_id: int) -> Optional[Wine]:
    return db.query(Wine).filter(Wine.id == wine_id).first()


def get_wines(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    wine_type: Optional[str] = None,
    country: Optional[str] = None,
    min_vintage: Optional[int] = None,
    max_vintage: Optional[int] = None,
    min_rating: Optional[float] = None,
    search: Optional[str] = None,
) -> list[Wine]:
    query = db.query(Wine)

    if wine_type:
        query = query.filter(Wine.wine_type == wine_type.lower())
    if country:
        query = query.filter(Wine.country.ilike(f"%{country}%"))
    if min_vintage is not None:
        query = query.filter(Wine.vintage >= min_vintage)
    if max_vintage is not None:
        query = query.filter(Wine.vintage <= max_vintage)
    if min_rating is not None:
        query = query.filter(Wine.rating >= min_rating)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Wine.name.ilike(pattern)
            | Wine.winery.ilike(pattern)
            | Wine.region.ilike(pattern)
            | Wine.grape_variety.ilike(pattern)
        )

    return query.offset(skip).limit(limit).all()


def create_wine(db: Session, wine: WineCreate) -> Wine:
    db_wine = Wine(**wine.model_dump())
    db.add(db_wine)
    db.commit()
    db.refresh(db_wine)
    return db_wine


def update_wine(db: Session, wine_id: int, wine: WineUpdate) -> Optional[Wine]:
    db_wine = get_wine(db, wine_id)
    if db_wine is None:
        return None
    update_data = wine.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_wine, field, value)
    db.commit()
    db.refresh(db_wine)
    return db_wine


def delete_wine(db: Session, wine_id: int) -> Optional[Wine]:
    db_wine = get_wine(db, wine_id)
    if db_wine is None:
        return None
    db.delete(db_wine)
    db.commit()
    return db_wine


def get_cellar_stats(db: Session) -> CellarStats:
    total_wines = db.query(func.count(Wine.id)).scalar()
    total_bottles = db.query(func.sum(Wine.quantity)).scalar() or 0
    avg_rating = db.query(func.avg(Wine.rating)).scalar()

    wines_by_type_rows = (
        db.query(Wine.wine_type, func.count(Wine.id))
        .group_by(Wine.wine_type)
        .all()
    )
    wines_by_type = {row[0]: row[1] for row in wines_by_type_rows}

    return CellarStats(
        total_wines=total_wines,
        total_bottles=int(total_bottles),
        average_rating=round(avg_rating, 2) if avg_rating is not None else None,
        wines_by_type=wines_by_type,
    )
