#!/usr/bin/env python3
"""
build_database.py

Genere la base SQLite du moteur : lego_engine.db.

C'est une COPIE OPTIMISEE de piece_types_master.csv, pas une nouvelle
source de verite : si le catalogue maitre change, on relance ce script.

Trois tables, comme demande :

  piece_types    : les 169 types fonctionnels (engine_id = cle stable
                   que le reste du moteur utilisera, jamais un
                   part_num Rebrickable).

  piece_variants : les references Rebrickable individuelles qui se
                   rangent derriere chaque engine_id (utile pour
                   remonter a la donnee source / debug, mais le
                   moteur ne doit normalement jamais avoir besoin d'y
                   toucher directement).

  piece_colors   : pour chaque variante, les couleurs reellement
                   disponibles - reconstruit directement depuis
                   elements.csv (pas en re-parsant du texte) pour
                   recuperer le vrai color_id ET le element_id
                   (= la reference commerciale LEGO/element utilisee
                   pour verifier la disponibilite chez un fournisseur
                   comme GoBricks).

Entrees :
  - piece_types_master.csv  (source de verite, genere par build_master_catalog.py)
  - piece_variants.csv      (mapping engine type -> part_num Rebrickable,
                              genere par normalize_types.py)
  - elements.csv, colors.csv (donnees brutes Rebrickable)

Sortie :
  - lego_engine.db (SQLite)

Usage:
    python3 build_database.py
"""

import csv
import sqlite3
from collections import defaultdict

MASTER_CSV = "piece_types_master.csv"
VARIANTS_CSV = "piece_variants.csv"
ELEMENTS_CSV = "elements.csv"
COLORS_CSV = "colors.csv"

DB_PATH = "lego_engine.db"

SCHEMA = """
CREATE TABLE piece_types (
    engine_id               TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    category                TEXT NOT NULL,
    width_studs             REAL,
    length_studs            REAL,
    height_studs            REAL,
    status                  TEXT NOT NULL CHECK (status IN ('ACTIVE','EXPERIMENTAL','DEPRECATED')),
    priority                INTEGER NOT NULL,
    num_rebrickable_variants INTEGER,
    num_colors_available     INTEGER
);

CREATE TABLE piece_variants (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    engine_id           TEXT NOT NULL REFERENCES piece_types(engine_id),
    rebrickable_part_num TEXT NOT NULL,
    rebrickable_name     TEXT NOT NULL,
    UNIQUE(rebrickable_part_num)
);

CREATE TABLE piece_colors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id   INTEGER NOT NULL REFERENCES piece_variants(id),
    color_id     TEXT NOT NULL,
    color_name   TEXT NOT NULL,
    rgb          TEXT,
    is_trans     TEXT,
    element_id   TEXT
);

CREATE INDEX idx_piece_variants_engine_id ON piece_variants(engine_id);
CREATE INDEX idx_piece_colors_variant_id ON piece_colors(variant_id);
CREATE INDEX idx_piece_colors_color_id ON piece_colors(color_id);
"""


def to_float(value):
    """Convertit '2', '2.5' ou une fraction type '2/3' en float. None si vide."""
    if not value:
        return None
    value = value.strip()
    if "/" in value:
        num, denom = value.split("/", 1)
        return float(num) / float(denom)
    return float(value)


def load_colors():
    """color_id -> {name, rgb, is_trans}"""
    colors = {}
    with open(COLORS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            colors[row["id"]] = {
                "name": row["name"],
                "rgb": row["rgb"],
                "is_trans": row["is_trans"],
            }
    return colors


def load_elements_by_part():
    """part_num -> list of (element_id, color_id)"""
    elements = defaultdict(list)
    with open(ELEMENTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            part_num = row["part_num"]
            if part_num:
                elements[part_num].append((row["element_id"], row["color_id"]))
    return elements


def main():
    with open(MASTER_CSV, newline="", encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))
    valid_engine_ids = {r["engine_id"] for r in master_rows}

    with open(VARIANTS_CSV, newline="", encoding="utf-8") as f:
        all_variant_rows = list(csv.DictReader(f))
    # normalize_types.py utilise des type_id (T0001...) dans piece_variants.csv ;
    # on doit les faire correspondre aux engine_id du fichier maitre via piece_types.csv
    with open("piece_types.csv", newline="", encoding="utf-8") as f:
        type_id_to_engine_id = {r["type_id"]: r["type_code"] for r in csv.DictReader(f)}

    variant_rows = []
    for r in all_variant_rows:
        engine_id = type_id_to_engine_id.get(r["type_id"])
        if engine_id in valid_engine_ids:
            variant_rows.append({**r, "engine_id": engine_id})

    colors = load_colors()
    elements_by_part = load_elements_by_part()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript("DROP TABLE IF EXISTS piece_colors;"
                        "DROP TABLE IF EXISTS piece_variants;"
                        "DROP TABLE IF EXISTS piece_types;")
    conn.executescript(SCHEMA)
    cur = conn.cursor()

    # --- piece_types ---
    cur.executemany(
        """INSERT INTO piece_types
           (engine_id, name, category, width_studs, length_studs, height_studs,
            status, priority, num_rebrickable_variants, num_colors_available)
           VALUES (:engine_id, :name, :category, :width_studs, :length_studs,
                   :height_studs, :status, :priority, :num_rebrickable_variants,
                   :num_colors_available)""",
        [
            {
                "engine_id": r["engine_id"],
                "name": r["name"],
                "category": r["category"],
                "width_studs": to_float(r["width_studs"]),
                "length_studs": to_float(r["length_studs"]),
                "height_studs": to_float(r["height_studs"]),
                "status": r["status"],
                "priority": int(r["priority"]),
                "num_rebrickable_variants": int(r["num_rebrickable_variants"]),
                "num_colors_available": int(r["num_colors_available"]),
            }
            for r in master_rows
        ],
    )

    # --- piece_variants ---
    # dedoublonnage defensif : un meme part_num ne doit apparaitre qu'une fois
    seen_parts = set()
    dedup_variant_rows = []
    for r in variant_rows:
        if r["part_num"] in seen_parts:
            continue
        seen_parts.add(r["part_num"])
        dedup_variant_rows.append(r)

    cur.executemany(
        """INSERT INTO piece_variants (engine_id, rebrickable_part_num, rebrickable_name)
           VALUES (:engine_id, :part_num, :rebrickable_name)""",
        dedup_variant_rows,
    )

    # id SQLite genere -> part_num, pour rattacher piece_colors
    cur.execute("SELECT id, rebrickable_part_num FROM piece_variants")
    variant_id_by_part = {part_num: vid for vid, part_num in cur.fetchall()}

    # --- piece_colors --- (reconstruit depuis elements.csv, pas depuis du texte)
    color_rows = []
    missing_color_ref = 0
    for part_num, variant_id in variant_id_by_part.items():
        for element_id, color_id in elements_by_part.get(part_num, []):
            c = colors.get(color_id)
            if not c:
                missing_color_ref += 1
                continue
            color_rows.append(
                {
                    "variant_id": variant_id,
                    "color_id": color_id,
                    "color_name": c["name"],
                    "rgb": c["rgb"],
                    "is_trans": c["is_trans"],
                    "element_id": element_id,
                }
            )

    cur.executemany(
        """INSERT INTO piece_colors (variant_id, color_id, color_name, rgb, is_trans, element_id)
           VALUES (:variant_id, :color_id, :color_name, :rgb, :is_trans, :element_id)""",
        color_rows,
    )

    conn.commit()

    # --- Rapport ---
    n_types = cur.execute("SELECT COUNT(*) FROM piece_types").fetchone()[0]
    n_variants = cur.execute("SELECT COUNT(*) FROM piece_variants").fetchone()[0]
    n_colors = cur.execute("SELECT COUNT(*) FROM piece_colors").fetchone()[0]
    n_distinct_colors = cur.execute("SELECT COUNT(DISTINCT color_id) FROM piece_colors").fetchone()[0]

    print(f"Base generee : {DB_PATH}")
    print(f"  piece_types    : {n_types} lignes")
    print(f"  piece_variants : {n_variants} lignes")
    print(f"  piece_colors   : {n_colors} lignes  ({n_distinct_colors} couleurs distinctes utilisees)")
    if missing_color_ref:
        print(f"  (! {missing_color_ref} lignes elements.csv ignorees : color_id absent de colors.csv)")

    print("\nExemple - couleurs disponibles pour BRICK_2X4 :")
    for row in cur.execute(
        """SELECT DISTINCT pc.color_name
           FROM piece_colors pc
           JOIN piece_variants pv ON pv.id = pc.variant_id
           WHERE pv.engine_id = 'BRICK_2X4'
           ORDER BY pc.color_name
           LIMIT 10"""
    ):
        print(f"  - {row[0]}")

    conn.close()


if __name__ == "__main__":
    main()
