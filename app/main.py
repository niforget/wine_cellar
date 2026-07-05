"""
Cave a vin partagee - backend FastAPI.

Sert l'API REST (sous /api/...) et l'interface web statique (sous /).
Concu pour tourner comme add-on Home Assistant, accessible via l'ingress
HA (auth deleguee) aussi bien depuis Safari iPhone que depuis un PC.
"""
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from database import get_db, init_db_if_needed, new_id, now, rows_to_list, row_to_dict, PHOTOS_DIR
import ocr as ocr_module
import ia_enrichissement

app = FastAPI(title="Cave a vin partagee")

STATIC_DIR = Path(__file__).parent / "static"


@app.on_event("startup")
def startup():
    init_db_if_needed()


def utilisateur_courant(x_utilisateur_id: Optional[str] = Header(default=None)) -> Optional[str]:
    """L'id de l'habitant courant, transmis par le frontend (pas d'auth
    mot de passe : l'acces est deja protege par l'ingress/reseau local HA)."""
    return x_utilisateur_id


# ---------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------
class UtilisateurIn(BaseModel):
    nom: str
    role: str = "membre"


@app.get("/api/utilisateurs")
def liste_utilisateurs():
    with get_db() as db:
        rows = db.execute("SELECT * FROM utilisateur WHERE actif = 1 ORDER BY nom").fetchall()
        return rows_to_list(rows)


@app.post("/api/utilisateurs")
def creer_utilisateur(u: UtilisateurIn):
    with get_db() as db:
        uid = new_id()
        db.execute(
            "INSERT INTO utilisateur (id, nom, role, actif, created_at, updated_at) VALUES (?,?,?,1,?,?)",
            (uid, u.nom, u.role, now(), now()),
        )
        return {"id": uid}


# ---------------------------------------------------------------------
# Caves
# ---------------------------------------------------------------------
class CaveIn(BaseModel):
    nom: str
    lignes: int = 1
    colonnes: int = 1
    legende: int = 0
    agencement: int = 0
    modele: Optional[str] = None
    commentaires: Optional[str] = None


def _generer_grille(db, cave_id: str, lignes: int, colonnes: int):
    """Cree les emplacements manquants pour couvrir lignes x colonnes."""
    existants = {
        (r["ligne"], r["colonne"])
        for r in db.execute("SELECT ligne, colonne FROM emplacement WHERE cave_id = ?", (cave_id,))
    }
    for l in range(lignes):
        for c in range(colonnes):
            if (l, c) not in existants:
                db.execute(
                    "INSERT INTO emplacement (id, cave_id, ligne, colonne) VALUES (?,?,?,?)",
                    (new_id(), cave_id, l, c),
                )


@app.get("/api/caves")
def liste_caves():
    with get_db() as db:
        caves = rows_to_list(db.execute("SELECT * FROM cave ORDER BY nom").fetchall())
        for c in caves:
            occ = db.execute(
                "SELECT COUNT(*) AS n FROM emplacement WHERE cave_id = ? AND vin_id IS NOT NULL",
                (c["id"],),
            ).fetchone()["n"]
            c["emplacements_occupes"] = occ
            c["emplacements_total"] = c["lignes"] * c["colonnes"]
        return caves


@app.post("/api/caves")
def creer_cave(cave: CaveIn, x_utilisateur_id: Optional[str] = Header(default=None)):
    with get_db() as db:
        cid = new_id()
        db.execute(
            """INSERT INTO cave (id, nom, lignes, colonnes, legende, agencement, modele,
                                  commentaires, created_by, updated_by, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cid, cave.nom, cave.lignes, cave.colonnes, cave.legende, cave.agencement,
             cave.modele, cave.commentaires, x_utilisateur_id, x_utilisateur_id, now(), now()),
        )
        _generer_grille(db, cid, cave.lignes, cave.colonnes)
        return {"id": cid}


@app.get("/api/caves/{cave_id}")
def detail_cave(cave_id: str):
    with get_db() as db:
        c = db.execute("SELECT * FROM cave WHERE id = ?", (cave_id,)).fetchone()
        if not c:
            raise HTTPException(404, "Cave introuvable")
        return row_to_dict(c)


@app.put("/api/caves/{cave_id}")
def modifier_cave(cave_id: str, cave: CaveIn, x_utilisateur_id: Optional[str] = Header(default=None)):
    with get_db() as db:
        existe = db.execute("SELECT id FROM cave WHERE id = ?", (cave_id,)).fetchone()
        if not existe:
            raise HTTPException(404, "Cave introuvable")
        db.execute(
            """UPDATE cave SET nom=?, lignes=?, colonnes=?, legende=?, agencement=?, modele=?,
                                commentaires=?, updated_by=?, updated_at=? WHERE id=?""",
            (cave.nom, cave.lignes, cave.colonnes, cave.legende, cave.agencement, cave.modele,
             cave.commentaires, x_utilisateur_id, now(), cave_id),
        )
        _generer_grille(db, cave_id, cave.lignes, cave.colonnes)
        return {"ok": True}


@app.delete("/api/caves/{cave_id}")
def supprimer_cave(cave_id: str):
    with get_db() as db:
        occ = db.execute(
            "SELECT COUNT(*) AS n FROM emplacement WHERE cave_id = ? AND vin_id IS NOT NULL",
            (cave_id,),
        ).fetchone()["n"]
        if occ > 0:
            raise HTTPException(400, "Cette cave contient encore des bouteilles assignees.")
        db.execute("DELETE FROM cave WHERE id = ?", (cave_id,))
        return {"ok": True}


@app.get("/api/caves/{cave_id}/emplacements")
def emplacements_cave(cave_id: str):
    with get_db() as db:
        rows = db.execute(
            """SELECT e.*, v.nom AS vin_nom, v.millesime AS vin_millesime
               FROM emplacement e LEFT JOIN vin v ON v.id = e.vin_id
               WHERE e.cave_id = ? ORDER BY e.ligne, e.colonne""",
            (cave_id,),
        ).fetchall()
        return rows_to_list(rows)


class EmplacementIn(BaseModel):
    vin_id: Optional[str] = None


@app.put("/api/emplacements/{emplacement_id}")
def assigner_emplacement(emplacement_id: str, e: EmplacementIn):
    with get_db() as db:
        existe = db.execute("SELECT id FROM emplacement WHERE id = ?", (emplacement_id,)).fetchone()
        if not existe:
            raise HTTPException(404, "Emplacement introuvable")
        db.execute("UPDATE emplacement SET vin_id = ? WHERE id = ?", (e.vin_id, emplacement_id))
        return {"ok": True}


# ---------------------------------------------------------------------
# Tiers (producteurs / vendeurs)
# ---------------------------------------------------------------------
class TiersIn(BaseModel):
    nom: str
    est_producteur: bool = False
    est_vendeur: bool = False
    email: Optional[str] = None
    telephone: Optional[str] = None
    site_web: Optional[str] = None
    ville: Optional[str] = None
    commentaires: Optional[str] = None


@app.get("/api/tiers")
def liste_tiers(type: Optional[str] = None):
    with get_db() as db:
        if type == "producteur":
            rows = db.execute("SELECT * FROM tiers WHERE est_producteur = 1 ORDER BY nom").fetchall()
        elif type == "vendeur":
            rows = db.execute("SELECT * FROM tiers WHERE est_vendeur = 1 ORDER BY nom").fetchall()
        else:
            rows = db.execute("SELECT * FROM tiers ORDER BY nom").fetchall()
        return rows_to_list(rows)


@app.post("/api/tiers")
def creer_tiers(t: TiersIn):
    with get_db() as db:
        tid = new_id()
        db.execute(
            """INSERT INTO tiers (id, nom, est_producteur, est_vendeur, email, telephone,
                                   site_web, ville, commentaires, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, t.nom, int(t.est_producteur), int(t.est_vendeur), t.email, t.telephone,
             t.site_web, t.ville, t.commentaires, now(), now()),
        )
        return {"id": tid}


# ---------------------------------------------------------------------
# Vins
# ---------------------------------------------------------------------
class VinIn(BaseModel):
    nom: str
    cuvee: Optional[str] = None
    millesime: Optional[int] = None
    producteur_id: Optional[str] = None
    appellation_id: Optional[str] = None
    region_id: Optional[str] = None
    pays_id: Optional[str] = None
    couleur_id: Optional[str] = None
    composition: Optional[str] = None
    degre_alcool: Optional[float] = None
    temp_service_min: Optional[float] = None
    temp_service_max: Optional[float] = None
    prix_estime: Optional[float] = None
    note: Optional[float] = None
    favori: bool = False
    tags: Optional[str] = None
    commentaires: Optional[str] = None
    statut: str = "actif"


@app.get("/api/vins")
def liste_vins(recherche: Optional[str] = None, statut: Optional[str] = None):
    with get_db() as db:
        sql = """SELECT v.*, COALESCE(s.stock_actuel, 0) AS stock_actuel
                  FROM vin v LEFT JOIN vin_stock s ON s.vin_id = v.id WHERE 1=1"""
        params = []
        if recherche:
            sql += " AND v.nom LIKE ?"
            params.append(f"%{recherche}%")
        if statut:
            sql += " AND v.statut = ?"
            params.append(statut)
        sql += " ORDER BY v.nom"
        rows = db.execute(sql, params).fetchall()
        return rows_to_list(rows)


@app.post("/api/vins")
def creer_vin(v: VinIn, x_utilisateur_id: Optional[str] = Header(default=None)):
    with get_db() as db:
        vid = new_id()
        db.execute(
            """INSERT INTO vin (id, nom, cuvee, millesime, producteur_id, appellation_id, region_id,
                                 pays_id, couleur_id, composition, degre_alcool, temp_service_min,
                                 temp_service_max, prix_estime, note, favori, tags, commentaires,
                                 statut, created_by, updated_by, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (vid, v.nom, v.cuvee, v.millesime, v.producteur_id, v.appellation_id, v.region_id,
             v.pays_id, v.couleur_id, v.composition, v.degre_alcool, v.temp_service_min,
             v.temp_service_max, v.prix_estime, v.note, int(v.favori), v.tags, v.commentaires,
             v.statut, x_utilisateur_id, x_utilisateur_id, now(), now()),
        )
        return {"id": vid}


@app.get("/api/vins/{vin_id}")
def detail_vin(vin_id: str):
    with get_db() as db:
        v = db.execute(
            """SELECT v.*, COALESCE(s.stock_actuel, 0) AS stock_actuel
               FROM vin v LEFT JOIN vin_stock s ON s.vin_id = v.id WHERE v.id = ?""",
            (vin_id,),
        ).fetchone()
        if not v:
            raise HTTPException(404, "Vin introuvable")
        vin = row_to_dict(v)
        vin["photos"] = rows_to_list(
            db.execute(
                "SELECT * FROM document WHERE parent_type='vin' AND parent_id=? ORDER BY ordre",
                (vin_id,),
            ).fetchall()
        )
        vin["emplacements"] = rows_to_list(
            db.execute(
                """SELECT e.*, c.nom AS cave_nom FROM emplacement e
                   JOIN cave c ON c.id = e.cave_id WHERE e.vin_id = ?""",
                (vin_id,),
            ).fetchall()
        )
        return vin


@app.put("/api/vins/{vin_id}")
def modifier_vin(vin_id: str, v: VinIn, x_utilisateur_id: Optional[str] = Header(default=None)):
    with get_db() as db:
        existe = db.execute("SELECT id FROM vin WHERE id = ?", (vin_id,)).fetchone()
        if not existe:
            raise HTTPException(404, "Vin introuvable")
        db.execute(
            """UPDATE vin SET nom=?, cuvee=?, millesime=?, producteur_id=?, appellation_id=?,
                               region_id=?, pays_id=?, couleur_id=?, composition=?, degre_alcool=?,
                               temp_service_min=?, temp_service_max=?, prix_estime=?, note=?,
                               favori=?, tags=?, commentaires=?, statut=?, updated_by=?, updated_at=?
               WHERE id=?""",
            (v.nom, v.cuvee, v.millesime, v.producteur_id, v.appellation_id, v.region_id, v.pays_id,
             v.couleur_id, v.composition, v.degre_alcool, v.temp_service_min, v.temp_service_max,
             v.prix_estime, v.note, int(v.favori), v.tags, v.commentaires, v.statut,
             x_utilisateur_id, now(), vin_id),
        )
        return {"ok": True}


@app.delete("/api/vins/{vin_id}")
def supprimer_vin(vin_id: str):
    with get_db() as db:
        db.execute("DELETE FROM vin WHERE id = ?", (vin_id,))
        return {"ok": True}


# ---------------------------------------------------------------------
# Mouvements de stock (achats, consommation, degustation, casse, don...)
# ---------------------------------------------------------------------
class MouvementIn(BaseModel):
    type_mouvement: str  # achat | consommation | degustation | casse | don | ajustement
    quantite: int
    date_mouvement: Optional[int] = None
    prix_unitaire: Optional[float] = None
    devise: str = "EUR"
    tiers_id: Optional[str] = None
    occasion: Optional[str] = None
    commentaires: Optional[str] = None


TYPES_MOUVEMENT_VALIDES = {"achat", "consommation", "degustation", "casse", "don", "ajustement"}


@app.get("/api/vins/{vin_id}/mouvements")
def liste_mouvements(vin_id: str):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM mouvement_stock WHERE vin_id = ? ORDER BY date_mouvement DESC",
            (vin_id,),
        ).fetchall()
        return rows_to_list(rows)


@app.post("/api/vins/{vin_id}/mouvements")
def creer_mouvement(vin_id: str, m: MouvementIn, x_utilisateur_id: Optional[str] = Header(default=None)):
    if m.type_mouvement not in TYPES_MOUVEMENT_VALIDES:
        raise HTTPException(400, f"type_mouvement invalide, attendu parmi {sorted(TYPES_MOUVEMENT_VALIDES)}")
    with get_db() as db:
        vin_existe = db.execute("SELECT id FROM vin WHERE id = ?", (vin_id,)).fetchone()
        if not vin_existe:
            raise HTTPException(404, "Vin introuvable")
        mid = new_id()
        db.execute(
            """INSERT INTO mouvement_stock (id, vin_id, type_mouvement, quantite, date_mouvement,
                                             prix_unitaire, devise, tiers_id, occasion, commentaires,
                                             utilisateur_id, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (mid, vin_id, m.type_mouvement, m.quantite, m.date_mouvement or now(), m.prix_unitaire,
             m.devise, m.tiers_id, m.occasion, m.commentaires, x_utilisateur_id, now()),
        )
        return {"id": mid}


@app.delete("/api/mouvements/{mouvement_id}")
def supprimer_mouvement(mouvement_id: str):
    with get_db() as db:
        db.execute("DELETE FROM mouvement_stock WHERE id = ?", (mouvement_id,))
        return {"ok": True}


# ---------------------------------------------------------------------
# Degustations
# ---------------------------------------------------------------------
class DegustationIn(BaseModel):
    date_degustation: Optional[int] = None
    note: Optional[float] = None
    commentaires: Optional[str] = None
    champs: Optional[str] = None  # JSON libre, encode cote frontend
    mouvement_stock_id: Optional[str] = None


@app.get("/api/vins/{vin_id}/degustations")
def liste_degustations(vin_id: str):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM degustation WHERE vin_id = ? ORDER BY date_degustation DESC",
            (vin_id,),
        ).fetchall()
        return rows_to_list(rows)


@app.post("/api/vins/{vin_id}/degustations")
def creer_degustation(vin_id: str, d: DegustationIn, x_utilisateur_id: Optional[str] = Header(default=None)):
    with get_db() as db:
        did = new_id()
        db.execute(
            """INSERT INTO degustation (id, vin_id, mouvement_stock_id, utilisateur_id,
                                         date_degustation, note, commentaires, champs, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (did, vin_id, d.mouvement_stock_id, x_utilisateur_id, d.date_degustation or now(),
             d.note, d.commentaires, d.champs, now()),
        )
        return {"id": did}


# ---------------------------------------------------------------------
# Documents (photos) + OCR
# ---------------------------------------------------------------------
@app.post("/api/documents")
async def televerser_document(
    fichier: UploadFile = File(...),
    parent_type: str = Form(...),
    parent_id: str = Form(...),
):
    ext = Path(fichier.filename or "photo.jpg").suffix or ".jpg"
    doc_id = new_id()
    nom_fichier = f"{doc_id}{ext}"
    chemin = Path(PHOTOS_DIR) / nom_fichier
    with open(chemin, "wb") as f:
        shutil.copyfileobj(fichier.file, f)

    with get_db() as db:
        db.execute(
            """INSERT INTO document (id, nom, type_contenu, parent_type, parent_id,
                                      chemin_fichier, ordre, created_at)
               VALUES (?,?,?,?,?,?,0,?)""",
            (doc_id, fichier.filename, fichier.content_type, parent_type, parent_id,
             f"photos/{nom_fichier}", now()),
        )
    return {"id": doc_id, "chemin_fichier": f"photos/{nom_fichier}"}


@app.get("/api/documents/{document_id}/fichier")
def telecharger_document(document_id: str):
    with get_db() as db:
        doc = db.execute("SELECT * FROM document WHERE id = ?", (document_id,)).fetchone()
        if not doc:
            raise HTTPException(404, "Document introuvable")
        chemin = Path(PHOTOS_DIR).parent / doc["chemin_fichier"]
        if not chemin.exists():
            raise HTTPException(404, "Fichier introuvable sur le disque")
        return FileResponse(chemin, media_type=doc["type_contenu"] or "image/jpeg")


@app.post("/api/vins/nouveau-depuis-photo")
async def nouveau_vin_depuis_photo(
    fichier: UploadFile = File(...),
    x_utilisateur_id: Optional[str] = Header(default=None),
):
    """Cree une fiche de vin en brouillon a partir d'une photo d'etiquette,
    et lance l'OCR dessus. Le frontend redirige ensuite vers l'edition de
    la fiche pour que l'habitant complete/valide (eventuellement via IA)."""
    vin_id = new_id()
    with get_db() as db:
        db.execute(
            """INSERT INTO vin (id, nom, statut, created_by, updated_by, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (vin_id, "Nouvelle fiche (a completer)", "brouillon",
             x_utilisateur_id, x_utilisateur_id, now(), now()),
        )

    ext = Path(fichier.filename or "photo.jpg").suffix or ".jpg"
    doc_id = new_id()
    nom_fichier = f"{doc_id}{ext}"
    chemin = Path(PHOTOS_DIR) / nom_fichier
    with open(chemin, "wb") as f:
        shutil.copyfileobj(fichier.file, f)

    texte_ocr = ocr_module.extraire_texte(str(chemin))

    with get_db() as db:
        db.execute(
            """INSERT INTO document (id, nom, type_contenu, parent_type, parent_id,
                                      chemin_fichier, ordre, created_at)
               VALUES (?,?,?,?,?,?,0,?)""",
            (doc_id, fichier.filename, fichier.content_type, "vin", vin_id,
             f"photos/{nom_fichier}", now()),
        )
        db.execute(
            "UPDATE vin SET ocr_texte_brut=?, ocr_traite_le=?, photo_principale_id=? WHERE id=?",
            (texte_ocr, now(), doc_id, vin_id),
        )

    return {"vin_id": vin_id, "document_id": doc_id, "texte_ocr": texte_ocr}


# ---------------------------------------------------------------------
# Enrichissement IA
# ---------------------------------------------------------------------
@app.post("/api/vins/{vin_id}/ia-enrichissement")
def lancer_enrichissement_ia(vin_id: str, x_utilisateur_id: Optional[str] = Header(default=None)):
    with get_db() as db:
        vin = db.execute("SELECT * FROM vin WHERE id = ?", (vin_id,)).fetchone()
        if not vin:
            raise HTTPException(404, "Vin introuvable")

        resultat = ia_enrichissement.enrichir_fiche(vin["nom"], vin["ocr_texte_brut"] or "")
        if not resultat["ok"]:
            raise HTTPException(502, resultat["erreur"])

        import json
        ia_id = new_id()
        db.execute(
            """INSERT INTO ia_enrichissement (id, vin_id, modele, champs_proposes, statut,
                                               utilisateur_id, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (ia_id, vin_id, resultat["modele"], json.dumps(resultat["champs"], ensure_ascii=False),
             "propose", x_utilisateur_id, now()),
        )
        return {"id": ia_id, "champs_proposes": resultat["champs"], "modele": resultat["modele"]}


class AppliquerIAIn(BaseModel):
    champs: dict


@app.post("/api/ia-enrichissement/{ia_id}/appliquer")
def appliquer_enrichissement_ia(ia_id: str, body: AppliquerIAIn, x_utilisateur_id: Optional[str] = Header(default=None)):
    import json
    with get_db() as db:
        ia = db.execute("SELECT * FROM ia_enrichissement WHERE id = ?", (ia_id,)).fetchone()
        if not ia:
            raise HTTPException(404, "Enregistrement introuvable")

        champs = body.champs
        vin_id = ia["vin_id"]
        maj = []
        valeurs = []
        mapping_simple = ["nom", "cuvee", "millesime", "composition", "degre_alcool", "commentaires"]
        for champ in mapping_simple:
            if champ in champs and champs[champ] not in (None, ""):
                maj.append(f"{champ} = ?")
                valeurs.append(champs[champ])
        if maj:
            valeurs.extend([now(), vin_id])
            db.execute(f"UPDATE vin SET {', '.join(maj)}, updated_at = ? WHERE id = ?", valeurs)

        db.execute("UPDATE vin SET ia_enrichi = 1, ia_traite_le = ? WHERE id = ?", (now(), vin_id))
        db.execute(
            "UPDATE ia_enrichissement SET statut='accepte', champs_appliques=?, traite_at=? WHERE id=?",
            (json.dumps(champs, ensure_ascii=False), now(), ia_id),
        )
        return {"ok": True}


# ---------------------------------------------------------------------
# Frontend statique
# ---------------------------------------------------------------------
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
