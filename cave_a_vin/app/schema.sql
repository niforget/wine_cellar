-- =====================================================================
-- Cave à vin partagée — schéma de base de données (v1)
-- Remplace PLOC. Conçu pour être hébergé sur Raspberry Pi (Home Assistant),
-- utilisé simultanément depuis plusieurs iPhones et un PC.
--
-- Principe central : cette base est la SEULE source de vérité.
-- Il n'y a pas de copie locale par appareil, donc pas de fusion à faire
-- ni de conflits possibles (contrairement à Ploud/PLOC).
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Utilisateurs (habitants de la maison)
-- ---------------------------------------------------------------------
CREATE TABLE utilisateur (
    id              TEXT PRIMARY KEY,
    nom             TEXT NOT NULL,
    ha_user_id      TEXT UNIQUE,              -- id de l'utilisateur Home Assistant, si l'auth est déléguée à HA
    avatar_document_id TEXT,                  -- FK vers document, ajoutée après création de la table document
    role            TEXT NOT NULL DEFAULT 'membre' CHECK (role IN ('admin', 'membre')),
    actif           INTEGER NOT NULL DEFAULT 1,
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL
);

-- ---------------------------------------------------------------------
-- Documents (photos d'étiquettes, de cave, logos de domaines...)
-- Table polymorphe : parent_type + parent_id désignent l'objet rattaché.
-- Le contenu du fichier n'est PAS stocké en base : seul le chemin l'est.
-- ---------------------------------------------------------------------
CREATE TABLE document (
    id              TEXT PRIMARY KEY,
    nom             TEXT,
    type_contenu    TEXT,                     -- ex: image/jpeg
    parent_type     TEXT NOT NULL CHECK (parent_type IN ('vin', 'cave', 'tiers', 'degustation', 'utilisateur')),
    parent_id       TEXT NOT NULL,
    chemin_fichier  TEXT NOT NULL,
    largeur         INTEGER,
    hauteur         INTEGER,
    ordre           INTEGER NOT NULL DEFAULT 0,
    created_at      INTEGER NOT NULL
);
CREATE INDEX idx_document_parent ON document(parent_type, parent_id);

-- ---------------------------------------------------------------------
-- Tables de référence (peuvent être importées telles quelles depuis PLOC)
-- ---------------------------------------------------------------------
CREATE TABLE pays (
    id      TEXT PRIMARY KEY,
    nom     TEXT NOT NULL
);

CREATE TABLE region (
    id          TEXT PRIMARY KEY,
    nom         TEXT NOT NULL,
    pays_id     TEXT REFERENCES pays(id)
);

CREATE TABLE appellation (
    id          TEXT PRIMARY KEY,
    nom         TEXT NOT NULL,
    region_id   TEXT REFERENCES region(id)
);

CREATE TABLE cepage (
    id      TEXT PRIMARY KEY,
    nom     TEXT NOT NULL
);

CREATE TABLE categorie (
    id      TEXT PRIMARY KEY,
    nom     TEXT NOT NULL
);

CREATE TABLE classification (
    id      TEXT PRIMARY KEY,
    nom     TEXT NOT NULL
);

CREATE TABLE couleur (
    id      TEXT PRIMARY KEY,
    nom     TEXT NOT NULL,
    r       INTEGER,
    g       INTEGER,
    b       INTEGER
);

CREATE TABLE format_bouteille (
    id          TEXT PRIMARY KEY,
    nom         TEXT NOT NULL,
    volume_ml   INTEGER
);

-- ---------------------------------------------------------------------
-- Tiers : producteurs (domaines) et vendeurs (cavistes, sites marchands).
-- PLOC avait deux tables séparées (owner / vendor) alors qu'un même
-- domaine peut être à la fois producteur et point de vente : ici une
-- seule table avec deux drapeaux.
-- ---------------------------------------------------------------------
CREATE TABLE tiers (
    id              TEXT PRIMARY KEY,
    nom             TEXT NOT NULL,
    est_producteur  INTEGER NOT NULL DEFAULT 0,
    est_vendeur     INTEGER NOT NULL DEFAULT 0,
    contact         TEXT,
    email           TEXT,
    telephone       TEXT,
    site_web        TEXT,
    adresse1        TEXT,
    adresse2        TEXT,
    ville           TEXT,
    code_postal     TEXT,
    pays_id         TEXT REFERENCES pays(id),
    latitude        REAL,
    longitude       REAL,
    commentaires    TEXT,
    logo_document_id TEXT REFERENCES document(id),
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL
);

-- ---------------------------------------------------------------------
-- Cave : un casier/meuble de rangement physique (ex : "Côté rue",
-- "Côté jardin", "Côté maison" — reprend directement le principe des
-- "racks" de PLOC : une grille de lignes x colonnes).
-- ---------------------------------------------------------------------
CREATE TABLE cave (
    id              TEXT PRIMARY KEY,
    nom             TEXT NOT NULL,
    lignes          INTEGER NOT NULL DEFAULT 1,
    colonnes        INTEGER NOT NULL DEFAULT 1,
    legende         INTEGER NOT NULL DEFAULT 0,   -- affichage lettres/chiffres (repris de PLOC.rack.legend)
    agencement      INTEGER NOT NULL DEFAULT 0,   -- mode de nommage des cases (repris de PLOC.rack.naming)
    modele          TEXT,                          -- référence libre au modèle de meuble
    commentaires    TEXT,
    photo_document_id TEXT REFERENCES document(id),
    created_by      TEXT REFERENCES utilisateur(id),
    updated_by      TEXT REFERENCES utilisateur(id),
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL
);

-- ---------------------------------------------------------------------
-- Vin : fiche de vin
-- ---------------------------------------------------------------------
CREATE TABLE vin (
    id                  TEXT PRIMARY KEY,
    nom                 TEXT NOT NULL,
    cuvee               TEXT,
    millesime           INTEGER,
    producteur_id       TEXT REFERENCES tiers(id),
    categorie_id        TEXT REFERENCES categorie(id),
    classification_id   TEXT REFERENCES classification(id),
    format_bouteille_id TEXT REFERENCES format_bouteille(id),
    appellation_id      TEXT REFERENCES appellation(id),
    region_id           TEXT REFERENCES region(id),
    pays_id             TEXT REFERENCES pays(id),
    couleur_id          TEXT REFERENCES couleur(id),
    composition         TEXT,                  -- texte libre, ex: "95% Cabernet Franc, 5% Cabernet Sauvignon"
    degre_alcool        REAL,
    temp_service_min    REAL,
    temp_service_max    REAL,
    consommer_debut     INTEGER,               -- année
    consommer_fin       INTEGER,
    apogee_debut        INTEGER,
    apogee_fin          INTEGER,
    prix_estime         REAL,
    devise              TEXT DEFAULT 'EUR',
    note                REAL,
    favori              INTEGER NOT NULL DEFAULT 0,
    tags                TEXT,
    commentaires        TEXT,

    statut              TEXT NOT NULL DEFAULT 'actif' CHECK (statut IN ('brouillon', 'actif', 'archive')),
    -- 'brouillon' = fiche créée automatiquement par OCR/IA, en attente de validation par un habitant

    -- OCR (photo d'étiquette prise au téléphone ou webcam PC)
    ocr_texte_brut      TEXT,
    ocr_traite_le       INTEGER,

    -- Enrichissement IA
    ia_enrichi          INTEGER NOT NULL DEFAULT 0,
    ia_traite_le        INTEGER,
    ia_modele           TEXT,

    -- Intégrations e-commerce (reprises de PLOC, optionnelles)
    app_source          TEXT,
    app_sku             TEXT,
    url_produit         TEXT,

    photo_principale_id TEXT REFERENCES document(id),

    created_by          TEXT REFERENCES utilisateur(id),
    updated_by          TEXT REFERENCES utilisateur(id),
    created_at          INTEGER NOT NULL,
    updated_at          INTEGER NOT NULL
);
CREATE INDEX idx_vin_statut ON vin(statut);
CREATE INDEX idx_vin_nom ON vin(nom);
CREATE INDEX idx_vin_producteur ON vin(producteur_id);

-- Composition structurée optionnelle (cépages + %), en plus du champ texte libre ci-dessus
CREATE TABLE vin_cepage (
    vin_id      TEXT NOT NULL REFERENCES vin(id) ON DELETE CASCADE,
    cepage_id   TEXT NOT NULL REFERENCES cepage(id),
    pourcentage REAL,
    PRIMARY KEY (vin_id, cepage_id)
);

-- ---------------------------------------------------------------------
-- Emplacement : une case précise dans une cave (occupée ou vide).
-- Plusieurs cases peuvent pointer vers le même vin (ex : une pile de
-- 6 bouteilles identiques) ; la quantité réelle est toujours calculée
-- via mouvement_stock, jamais déduite du nombre de cases.
-- ---------------------------------------------------------------------
CREATE TABLE emplacement (
    id          TEXT PRIMARY KEY,
    cave_id     TEXT NOT NULL REFERENCES cave(id) ON DELETE CASCADE,
    ligne       INTEGER NOT NULL,
    colonne     INTEGER NOT NULL,
    vin_id      TEXT REFERENCES vin(id) ON DELETE SET NULL,
    qrcode      TEXT,
    tags        TEXT,
    UNIQUE (cave_id, ligne, colonne)
);
CREATE INDEX idx_emplacement_vin ON emplacement(vin_id);

-- ---------------------------------------------------------------------
-- Historique d'enrichissement IA (traçabilité des suggestions faites
-- sur une fiche : ce qui a été proposé, par quel modèle, et ce que
-- l'utilisateur a finalement retenu).
-- ---------------------------------------------------------------------
CREATE TABLE ia_enrichissement (
    id                  TEXT PRIMARY KEY,
    vin_id              TEXT NOT NULL REFERENCES vin(id) ON DELETE CASCADE,
    modele              TEXT NOT NULL,
    champs_proposes     TEXT NOT NULL,   -- JSON { "champ": "valeur_proposee", ... }
    champs_appliques    TEXT,            -- JSON des champs effectivement retenus
    statut              TEXT NOT NULL DEFAULT 'propose' CHECK (statut IN ('propose', 'accepte', 'rejete', 'partiel')),
    utilisateur_id      TEXT REFERENCES utilisateur(id),
    created_at          INTEGER NOT NULL,
    traite_at           INTEGER
);
CREATE INDEX idx_ia_enrichissement_vin ON ia_enrichissement(vin_id);

-- ---------------------------------------------------------------------
-- Mouvements de stock : LA source de vérité pour la quantité de
-- bouteilles (achats, consommation, dégustation, casse, don, ajustement
-- d'inventaire). Le nombre de bouteilles en stock n'est jamais stocké
-- directement sur la fiche vin : il se calcule (voir vue vin_stock),
-- ce qui évite tout risque de désynchronisation.
-- ---------------------------------------------------------------------
CREATE TABLE mouvement_stock (
    id              TEXT PRIMARY KEY,
    vin_id          TEXT NOT NULL REFERENCES vin(id) ON DELETE CASCADE,
    type_mouvement  TEXT NOT NULL CHECK (type_mouvement IN ('achat', 'consommation', 'degustation', 'casse', 'don', 'ajustement')),
    quantite        INTEGER NOT NULL,   -- toujours positif ; le sens (+/-) dépend de type_mouvement
    date_mouvement  INTEGER NOT NULL,
    prix_unitaire   REAL,
    devise          TEXT DEFAULT 'EUR',
    tiers_id        TEXT REFERENCES tiers(id),   -- vendeur, pour un achat
    occasion        TEXT,               -- ex: "anniversaire", "repas de Noël"
    commentaires    TEXT,
    utilisateur_id  TEXT REFERENCES utilisateur(id),  -- qui a fait le mouvement
    created_at      INTEGER NOT NULL
);
CREATE INDEX idx_mouvement_vin ON mouvement_stock(vin_id);
CREATE INDEX idx_mouvement_date ON mouvement_stock(date_mouvement);
CREATE INDEX idx_mouvement_type ON mouvement_stock(type_mouvement);

-- Stock actuel par vin, calculé à la volée à partir des mouvements.
-- achat/ajustement (positif si quantite > 0) alimentent le stock ;
-- consommation/degustation/casse/don le diminuent.
CREATE VIEW vin_stock AS
SELECT
    vin.id AS vin_id,
    COALESCE(SUM(
        CASE
            WHEN m.type_mouvement IN ('achat', 'ajustement') THEN m.quantite
            ELSE -m.quantite
        END
    ), 0) AS stock_actuel
FROM vin
LEFT JOIN mouvement_stock m ON m.vin_id = vin.id
GROUP BY vin.id;

-- ---------------------------------------------------------------------
-- Dégustation : note de dégustation, éventuellement liée au mouvement
-- de stock qui correspond à l'ouverture de la bouteille.
-- Le champ JSON "champs" permet d'ajouter des critères libres
-- (arômes, accord mets-vin...) sans devoir modifier le schéma —
-- un système de gabarits (comme tastingnotestemplate dans PLOC)
-- pourra être ajouté plus tard si besoin.
-- ---------------------------------------------------------------------
CREATE TABLE degustation (
    id                  TEXT PRIMARY KEY,
    vin_id              TEXT NOT NULL REFERENCES vin(id) ON DELETE CASCADE,
    mouvement_stock_id  TEXT REFERENCES mouvement_stock(id) ON DELETE SET NULL,
    utilisateur_id      TEXT REFERENCES utilisateur(id),
    date_degustation    INTEGER NOT NULL,
    note                REAL,
    commentaires        TEXT,
    champs              TEXT,   -- JSON libre
    photo_document_id   TEXT REFERENCES document(id),
    created_at          INTEGER NOT NULL
);
CREATE INDEX idx_degustation_vin ON degustation(vin_id);

-- ---------------------------------------------------------------------
-- Paramètres globaux de l'application
-- ---------------------------------------------------------------------
CREATE TABLE parametre (
    cle         TEXT PRIMARY KEY,
    valeur      TEXT,
    updated_at  INTEGER NOT NULL
);
       