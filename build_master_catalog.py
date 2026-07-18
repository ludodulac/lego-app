#!/usr/bin/env python3
"""
build_master_catalog.py

Genere le fichier MAITRE du moteur : piece_types_master.csv.

Contrairement a piece_types.csv (sortie brute de la normalisation, qui
contient aussi les 654 types "rares"), ce fichier ne contient QUE les
169 types "coeur" retenus pour le MVP, avec :
  - engine_id      : identifiant stable et definitif (BRICK_2X4...),
                     c'est le seul identifiant que le moteur de
                     generation doit connaitre.
  - dimensions completees avec des conventions par defaut quand le nom
    Rebrickable ne les donnait pas explicitement (brique = 1 unite de
    hauteur, plate/tuile = 1/3 unite).
  - status  : ACTIVE / EXPERIMENTAL - EXPERIMENTAL quand une dimension
    cle est manquante et n'a pas de convention par defaut fiable
    (Windows and Doors), a completer/verifier a la main.
  - priority : 1 = briques/plates/tuiles de base (indispensables),
               2 = pieces de forme (pentes, fenetres/portes, baseplates).

Entree  : piece_types.csv (sortie de normalize_types.py)
Sortie  : piece_types_master.csv

Usage:
    python3 build_master_catalog.py
"""

import csv

INPUT_CSV = "piece_types.csv"
OUTPUT_CSV = "piece_types_master.csv"

# Hauteur par defaut (en unites "brique") quand non extraite du nom.
# 1 brique = 1.0 ; 1 plate/tuile = 1/3 de brique (convention LEGO standard).
DEFAULT_HEIGHT_BY_CATEGORY = {
    "Bricks": "1.0",
    "Bricks Sloped": "1.0",
    "Plates": "0.33",
    "Tiles": "0.33",
    "Baseplates": "0.33",
    # "Windows and Doors" : pas de convention fiable -> laisse vide si absent
}

PRIORITY_BY_CATEGORY = {
    "Bricks": 1,
    "Plates": 1,
    "Tiles": 1,
    "Bricks Sloped": 2,
    "Windows and Doors": 2,
    "Baseplates": 2,
}


def main():
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["tier"] == "core"]

    master_rows = []
    n_experimental = 0

    for r in rows:
        category = r["category"]
        width = r["width_studs"]
        length = r["length_studs"]
        height = r["height_studs"]

        status = "ACTIVE"

        if not height:
            default = DEFAULT_HEIGHT_BY_CATEGORY.get(category)
            if default is not None:
                height = default
            else:
                # Pas de convention fiable (ex: Windows and Doors) :
                # on laisse vide et on marque EXPERIMENTAL pour
                # signaler qu'il faut completer/verifier a la main.
                status = "EXPERIMENTAL"
                n_experimental += 1

        if not width or not length:
            # Dimension principale absente (ex: "Baseplate", "Door Sliding
            # - Type 1") : idem, a completer a la main.
            status = "EXPERIMENTAL"

        master_rows.append(
            {
                "engine_id": r["type_code"],
                "name": r["name"],
                "category": category,
                "width_studs": width,
                "length_studs": length,
                "height_studs": height,
                "status": status,
                "priority": PRIORITY_BY_CATEGORY.get(category, 2),
                "num_rebrickable_variants": r["num_rebrickable_variants"],
                "num_colors_available": r["num_colors_available"],
            }
        )

    # Tri : priorite, puis categorie, puis nombre de variantes (pertinence) desc
    master_rows.sort(
        key=lambda r: (r["priority"], r["category"], -int(r["num_rebrickable_variants"]))
    )

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "engine_id",
                "name",
                "category",
                "width_studs",
                "length_studs",
                "height_studs",
                "status",
                "priority",
                "num_rebrickable_variants",
                "num_colors_available",
            ],
        )
        writer.writeheader()
        writer.writerows(master_rows)

    # --- Rapport ---
    print(f"Types coeur importes : {len(master_rows)}")
    n_active = sum(1 for r in master_rows if r["status"] == "ACTIVE")
    print(f"  - ACTIVE       : {n_active}")
    print(f"  - EXPERIMENTAL : {n_experimental}  (dimension a completer a la main)")

    print("\nRepartition par priorite :")
    by_prio = {}
    for r in master_rows:
        by_prio.setdefault(r["priority"], []).append(r)
    for prio in sorted(by_prio):
        print(f"  priority {prio} : {len(by_prio[prio])} types")

    print("\nTypes EXPERIMENTAL (dimension manquante, a verifier) :")
    for r in master_rows:
        if r["status"] == "EXPERIMENTAL":
            print(
                f"  {r['engine_id']:35s} cat={r['category']:20s} "
                f"w={r['width_studs'] or '?'} l={r['length_studs'] or '?'} "
                f"h={r['height_studs'] or '?'}"
            )

    print(f"\n-> {OUTPUT_CSV} genere : source de verite du moteur ({len(master_rows)} types)")


if __name__ == "__main__":
    main()
