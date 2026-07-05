import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_wine_cellar.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


SAMPLE_WINE = {
    "name": "Château Margaux",
    "winery": "Château Margaux",
    "vintage": 2015,
    "wine_type": "red",
    "region": "Margaux",
    "country": "France",
    "grape_variety": "Cabernet Sauvignon",
    "quantity": 6,
    "rating": 98.0,
    "price": 750.0,
    "notes": "Exceptional vintage",
}


def test_add_wine():
    response = client.post("/wines", json=SAMPLE_WINE)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == SAMPLE_WINE["name"]
    assert data["wine_type"] == "red"
    assert data["vintage"] == 2015
    assert "id" in data


def test_list_wines_empty():
    response = client.get("/wines")
    assert response.status_code == 200
    assert response.json() == []


def test_list_wines():
    client.post("/wines", json=SAMPLE_WINE)
    response = client.get("/wines")
    assert response.status_code == 200
    wines = response.json()
    assert len(wines) == 1
    assert wines[0]["name"] == SAMPLE_WINE["name"]


def test_get_wine():
    created = client.post("/wines", json=SAMPLE_WINE).json()
    response = client.get(f"/wines/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_wine_not_found():
    response = client.get("/wines/9999")
    assert response.status_code == 404


def test_update_wine():
    created = client.post("/wines", json=SAMPLE_WINE).json()
    response = client.patch(f"/wines/{created['id']}", json={"quantity": 3, "rating": 95.0})
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 3
    assert data["rating"] == 95.0
    assert data["name"] == SAMPLE_WINE["name"]


def test_update_wine_not_found():
    response = client.patch("/wines/9999", json={"quantity": 1})
    assert response.status_code == 404


def test_delete_wine():
    created = client.post("/wines", json=SAMPLE_WINE).json()
    response = client.delete(f"/wines/{created['id']}")
    assert response.status_code == 200

    response = client.get(f"/wines/{created['id']}")
    assert response.status_code == 404


def test_delete_wine_not_found():
    response = client.delete("/wines/9999")
    assert response.status_code == 404


def test_filter_by_type():
    client.post("/wines", json=SAMPLE_WINE)
    white_wine = {**SAMPLE_WINE, "name": "Chablis", "wine_type": "white"}
    client.post("/wines", json=white_wine)

    response = client.get("/wines?wine_type=red")
    assert response.status_code == 200
    wines = response.json()
    assert len(wines) == 1
    assert wines[0]["wine_type"] == "red"


def test_filter_by_country():
    client.post("/wines", json=SAMPLE_WINE)
    italian_wine = {**SAMPLE_WINE, "name": "Barolo", "winery": "Gaja", "country": "Italy"}
    client.post("/wines", json=italian_wine)

    response = client.get("/wines?country=France")
    assert response.status_code == 200
    wines = response.json()
    assert len(wines) == 1
    assert wines[0]["country"] == "France"


def test_filter_by_vintage():
    client.post("/wines", json=SAMPLE_WINE)
    older_wine = {**SAMPLE_WINE, "name": "Old Wine", "vintage": 2005}
    client.post("/wines", json=older_wine)

    response = client.get("/wines?min_vintage=2010")
    assert response.status_code == 200
    wines = response.json()
    assert len(wines) == 1
    assert wines[0]["vintage"] == 2015


def test_filter_by_rating():
    client.post("/wines", json=SAMPLE_WINE)
    cheaper_wine = {**SAMPLE_WINE, "name": "Table Wine", "rating": 82.0}
    client.post("/wines", json=cheaper_wine)

    response = client.get("/wines?min_rating=95")
    assert response.status_code == 200
    wines = response.json()
    assert len(wines) == 1
    assert wines[0]["rating"] == 98.0


def test_search_wines():
    client.post("/wines", json=SAMPLE_WINE)
    other_wine = {**SAMPLE_WINE, "name": "Barolo", "winery": "Gaja", "region": "Piedmont"}
    client.post("/wines", json=other_wine)

    response = client.get("/wines?search=Margaux")
    assert response.status_code == 200
    wines = response.json()
    assert len(wines) == 1
    assert "Margaux" in wines[0]["name"]


def test_cellar_stats_empty():
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_wines"] == 0
    assert stats["total_bottles"] == 0
    assert stats["average_rating"] is None
    assert stats["wines_by_type"] == {}


def test_cellar_stats():
    client.post("/wines", json=SAMPLE_WINE)
    white_wine = {**SAMPLE_WINE, "name": "Chablis", "wine_type": "white", "quantity": 2, "rating": 90.0}
    client.post("/wines", json=white_wine)

    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_wines"] == 2
    assert stats["total_bottles"] == 8  # 6 + 2
    assert stats["average_rating"] == pytest.approx(94.0, abs=0.1)
    assert stats["wines_by_type"]["red"] == 1
    assert stats["wines_by_type"]["white"] == 1


def test_wine_type_case_insensitive():
    wine = {**SAMPLE_WINE, "wine_type": "RED"}
    response = client.post("/wines", json=wine)
    assert response.status_code == 201
    assert response.json()["wine_type"] == "red"


def test_invalid_wine_type():
    wine = {**SAMPLE_WINE, "wine_type": "beer"}
    response = client.post("/wines", json=wine)
    assert response.status_code == 422


def test_invalid_rating():
    wine = {**SAMPLE_WINE, "rating": 150.0}
    response = client.post("/wines", json=wine)
    assert response.status_code == 422


def test_invalid_vintage():
    wine = {**SAMPLE_WINE, "vintage": 1700}
    response = client.post("/wines", json=wine)
    assert response.status_code == 422


def test_pagination():
    for i in range(5):
        client.post("/wines", json={**SAMPLE_WINE, "name": f"Wine {i}"})

    response = client.get("/wines?limit=2&skip=0")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/wines?limit=2&skip=2")
    assert response.status_code == 200
    assert len(response.json()) == 2
