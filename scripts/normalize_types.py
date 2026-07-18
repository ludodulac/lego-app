#!/usr/bin/env python3
"""
normalize_types.py

Phase 1.5 - Normalisation des pieces.

Le moteur de generation ne doit pas raisonner en references Rebrickable
(3001, 3001a, 3001_old, 3001 with print...) mais en TYPES FONCTIONNELS
(BRICK_2X4). Ce script regroupe automatiquement les variantes qui sont
geometriquement identiques :
  - impressions / decorations / autocollants (print, pattern, sticker...)
  - moules / details de fabrication (groove, old type, hollow/solid studs,
    presence ou non de tubes/supports internes)

Entree  : mvp_catalog.csv (genere par build_mvp_catalog.py)
Sorties :
  - piece_types.csv     : un type fonctionnel par ligne (BRICK_2X4, TILE_2X2...)
  - piece_variants.csv  : mapping piece Rebrickable -> type fonctionnel

Usage:
    python3 normalize_types.py
"""

import csv
import re
from collections import defaultdict

INPUT_CSV = "mvp_catalog.csv"
TYPES_OUTPUT_CSV = "piece_types.csv"
VARIANTS_OUTPUT_CSV = "piece_variants.csv"

# Seuil pour distinguer un type "coeur" (reutilisable, plusieurs variantes
# Rebrickable derriere) d'un type "rare" (une seule variante = piece tres
# specifique a un set, candidate a "plus tard")
CORE_MIN_VARIANTS = 2

# --- Regex de nettoyage -----------------------------------------------

DECORATION_PATTERNS = [
    r"\(sticker\)",
    r"\[[^\]]*\]",  # notes entre crochets: [Plain], [Embossed], [343-2]...
    r"\bwith\b.*?\b(print|pattern|sticker|decorated|embossed)\b.*$",
    r"['\"].*$",  # texte entre guillemets (quasi toujours un texte imprime) + suite
    r"\b(print|pattern|sticker|decorated|embossed)\b.*$",
]

MOLD_NOISE_PATTERNS = [
    r"\bwithout\s+groove\b",
    r"\bwith\s+groove\b",
    r"\(old type\)",
    r"\bold\s+mold\b",
    r"\bwithout\s+bottom\s+tubes\b",
    r"\bwith\s+bottom\s+tubes\b",
    r"\bhollow\s+stud(s)?\b",
    r"\bsolid\s+stud(s)?\b",
    r"\bwith\s+(2\s+)?cross\s+side\s+supports?\b",
    r"\bwith\s+cross\s+supports?\b",
]

# Nettoyage final : ponctuation/mots orphelins laisses par les regex ci-dessus
TRAILING_JUNK_PATTERNS = [
    r"\bwith\s*$",
    r",\s*$",
    r",\s*,",
]


def clean_name(raw_name):
    n = raw_name
    for pat in DECORATION_PATTERNS:
        n = re.sub(pat, "", n, flags=re.I)
    for pat in MOLD_NOISE_PATTERNS:
        n = re.sub(pat, "", n, flags=re.I)
    # plusieurs passes pour les patterns de fin de chaine imbriques
    for _ in range(3):
        for pat in TRAILING_JUNK_PATTERNS:
            n = re.sub(pat, "", n, flags=re.I)
    n = re.sub(r"\s{2,}", " ", n).strip(" ,-")
    return n


def to_type_key(category, cleaned_name):
    """Cle de regroupement insensible a la casse (Brick 1 X 1 == Brick 1 x 1)."""
    normalized = re.sub(r"\s+", " ", cleaned_name.strip().lower())
    normalized = normalized.replace(" x ", " x ")  # no-op, garde lisible
    return (category, normalized)


def to_type_code(category, cleaned_name):
    """BRICK_2X4, TILE_2X2, WINDOWS_AND_DOORS_DOOR_1X3X1_LEFT, ..."""
    slug = re.sub(r"[^a-z0-9]+", "_", cleaned_name.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug).upper()
    # Compacte les dimensions ("2_X_4" -> "2X4") pour un engine_id lisible
    # et stable (convention BRICK_2X4 plutot que BRICK_2_X_4).
    prev = None
    while prev != slug:
        prev = slug
        slug = re.sub(r"(\d)_X_(\d)", r"\1X\2", slug)
    return slug


DIM_RE = re.compile(
    r"(\d+(?:/\d+)?)\s*x\s*(\d+(?:/\d+)?)(?:\s*x\s*(\d+(?:/\d+)?))?", re.I
)


def extract_dims(cleaned_name):
    """Extrait largeur/longueur/hauteur (en studs) depuis le nom nettoye, si presentes."""
    m = DIM_RE.search(cleaned_name)
    if not m:
        return "", "", ""
    return m.group(1) or "", m.group(2) or "", m.group(3) or ""


def main():
    rows = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    groups = defaultdict(list)
    cleaned_display = {}  # cle -> premier nom nettoye rencontre (pour affichage)

    for row in rows:
        cleaned = clean_name(row["name"])
        key = to_type_key(row["category"], cleaned)
        groups[key].append(row)
        cleaned_display.setdefault(key, cleaned)

    # --- piece_types.csv ---
    type_rows = []
    variant_rows = []

    # tri par nb de variantes desc, pour des type_id lisibles/stables
    sorted_groups = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    for idx, (key, variants) in enumerate(sorted_groups, start=1):
        category, _ = key
        display_name = cleaned_display[key]
        type_code = to_type_code(category, display_name)
        type_id = f"T{idx:04d}"
        width, length, height = extract_dims(display_name)
        n_variants = len(variants)
        tier = "core" if n_variants >= CORE_MIN_VARIANTS else "rare"

        all_colors = set()
        for v in variants:
            if v["colors_available"]:
                all_colors.update(v["colors_available"].split("|"))

        type_rows.append(
            {
                "type_id": type_id,
                "type_code": type_code,
                "name": display_name,
                "category": category,
                "width_studs": width,
                "length_studs": length,
                "height_studs": height,
                "tier": tier,
                "num_rebrickable_variants": n_variants,
                "num_colors_available": len(all_colors),
            }
        )

        for v in variants:
            variant_rows.append(
                {
                    "type_id": type_id,
                    "part_num": v["part_num"],
                    "rebrickable_name": v["name"],
                    "colors_available": v["colors_available"],
                }
            )

    with open(TYPES_OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "type_id",
                "type_code",
                "name",
                "category",
                "width_studs",
                "length_studs",
                "height_studs",
                "tier",
                "num_rebrickable_variants",
                "num_colors_available",
            ],
        )
        writer.writeheader()
        writer.writerows(type_rows)

    with open(VARIANTS_OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["type_id", "part_num", "rebrickable_name", "colors_available"]
        )
        writer.writeheader()
        writer.writerows(variant_rows)

    # --- Rapport ---
    n_core = sum(1 for t in type_rows if t["tier"] == "core")
    n_rare = sum(1 for t in type_rows if t["tier"] == "rare")
    pieces_core = sum(t["num_rebrickable_variants"] for t in type_rows if t["tier"] == "core")
    pieces_rare = sum(t["num_rebrickable_variants"] for t in type_rows if t["tier"] == "rare")
    total_pieces = pieces_core + pieces_rare

    print(f"Pieces en entree (mvp_catalog.csv)      : {len(rows)}")
    print(f"Types fonctionnels obtenus              : {len(type_rows)}")
    print(f"  - types 'coeur' (>= {CORE_MIN_VARIANTS} variantes)      : {n_core}"
          f"  -> couvrent {pieces_core} pieces ({100*pieces_core/total_pieces:.1f}%)")
    print(f"  - types 'rares' (1 seule variante)      : {n_rare}"
          f"  -> couvrent {pieces_rare} pieces ({100*pieces_rare/total_pieces:.1f}%)")
    print(f"\n-> {TYPES_OUTPUT_CSV} : catalogue de types (une ligne = un type fonctionnel)")
    print(f"-> {VARIANTS_OUTPUT_CSV} : mapping type -> references Rebrickable d'origine")

    print("\nTop 20 types 'coeur' les plus representes :")
    for t in sorted(type_rows, key=lambda t: -t["num_rebrickable_variants"])[:20]:
        print(
            f"  {t['type_id']}  {t['type_code']:35s} "
            f"({t['num_rebrickable_variants']:4d} variantes, "
            f"{t['num_colors_available']:3d} couleurs)"
        )


if __name__ == "__main__":
    main()
