# Wine Cellar Manager

A REST API for managing your personal wine collection, built with FastAPI and SQLite.

## Features

- **Add, update, and remove wines** from your cellar
- **Search** wines by name, winery, region, or grape variety
- **Filter** by wine type, country, vintage range, and minimum rating
- **Cellar statistics**: total wines, bottles, average rating, and breakdown by wine type
- **Automatic API docs** at `/docs` (Swagger UI)

## Wine Types

`red`, `white`, `rosé`, `sparkling`, `dessert`, `other`

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/wines` | List wines (with optional filters) |
| `POST` | `/wines` | Add a wine |
| `GET` | `/wines/{id}` | Get a wine by ID |
| `PATCH` | `/wines/{id}` | Update a wine |
| `DELETE` | `/wines/{id}` | Remove a wine |
| `GET` | `/stats` | Cellar statistics |

### Query Parameters for `GET /wines`

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search name, winery, region, grape variety |
| `wine_type` | string | Filter by type |
| `country` | string | Filter by country |
| `min_vintage` | int | Minimum vintage year |
| `max_vintage` | int | Maximum vintage year |
| `min_rating` | float | Minimum rating (0–100) |
| `skip` | int | Pagination offset |
| `limit` | int | Pagination limit (max 1000) |

## Example

```bash
# Add a wine
curl -X POST http://localhost:8000/wines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Château Margaux",
    "winery": "Château Margaux",
    "vintage": 2015,
    "wine_type": "red",
    "region": "Margaux",
    "country": "France",
    "grape_variety": "Cabernet Sauvignon",
    "quantity": 6,
    "rating": 98.0,
    "price": 750.0
  }'

# List all red wines
curl "http://localhost:8000/wines?wine_type=red"

# Search by name
curl "http://localhost:8000/wines?search=Margaux"

# Cellar statistics
curl http://localhost:8000/stats
```

## Tests

```bash
python -m pytest tests/ -v
```
