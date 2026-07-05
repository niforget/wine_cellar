"""
Acces a la base SQLite "cave a vin partagee".

DB_PATH et PHOTOS_DIR sont surchargeables via variables d'environnement
(voir config.yaml de l'add-on Home Assistant). Par defaut, tout vit sous
/data, qui est le volume persistant fourni par le superviseur HA pour
chaque add-on : il survit aux mises a jour et redemarrages du conteneur.
"""
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

DB_PATH = os.environ.get("CAVE_DB_PATH", "/data/cave_a_vin.sqlite")
PHOTOS_DIR = os.environ.get("CAVE_PHOTOS_DIR", "/data/photos")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def now() -> int:
    return int(time.time())


def new_id() -> str:
    return str(uuid.uuid4()).upper()


def init_db_if_needed():
    """Cree la base et le dossier photos au premier demarrage si absents."""
    Path(PHOTOS_DIR).mkdir(parents=True, exist_ok=True)
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    is_new = not Path(DB_PATH).exists()
    con = sqlite3.connect(DB_PATH)
    if is_new:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            con.executescript(f.read())
        # Un premier compte admin pour demarrer - modifiable ensuite dans l'appli
        con.execute(
            "INSERT INTO utilisateur (id, nom, role, actif, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (new_id(), "Admin", "admin", 1, now(), now()),
        )
        con.commit()
    con.close()


@contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()} if row else None


def rows_to_list(rows) -> list:
    return [row_to_dict(r) for r in rows]
