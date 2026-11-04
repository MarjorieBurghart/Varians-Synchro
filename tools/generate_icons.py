#!/usr/bin/env python3
"""Produit les icônes de l'application (``icons/``) à partir du logo.

Source : le fichier ``logo/*.psd`` (un seul). Pillow lit l'image fusionnée
du PSD : dans Photoshop, garder « Maximiser la compatibilité » à
l'enregistrement. Pillow n'est nécessaire qu'ici (``pip install Pillow``) ;
l'application lit les PNG produits avec Qt.

Le logo, rogné à son contenu, est centré sur une pastille blanche aux coins
arrondis : ses traits bleu marine restent lisibles sur une barre des tâches
sombre, et le liseré clair laissé par le détourage disparaît sur le blanc.

Usage : ``python tools/generate_icons.py`` (depuis la racine du dépôt).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from varians_synchro.app_icon import ICON_DIR, ICON_SIZES, icon_files  # noqa: E402

LOGO_SHARE = 0.84           # part du côté de la pastille occupée par le logo
CORNER = 0.20               # rayon des coins, en part du côté
MASTER = 1024               # côté de l'image de travail, réduite ensuite
SUPERSAMPLE = 4             # bords arrondis lissés


def source_logo() -> Path:
    found = sorted((ROOT / 'logo').glob('*.psd'))
    if len(found) != 1:
        raise SystemExit(f'Un seul fichier .psd attendu dans logo/ : {[p.name for p in found]}')
    return found[0]


def tile(logo: Image.Image) -> Image.Image:
    """Le logo centré sur la pastille blanche, en ``MASTER`` × ``MASTER``."""
    logo = logo.convert('RGBA')
    logo = logo.crop(logo.getchannel('A').getbbox())
    scale = MASTER * LOGO_SHARE / max(logo.size)
    logo = logo.resize((round(logo.width * scale), round(logo.height * scale)), Image.LANCZOS)
    big = MASTER * SUPERSAMPLE
    mask = Image.new('L', (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, big - 1, big - 1], radius=round(big * CORNER), fill=255)
    image = Image.new('RGBA', (MASTER, MASTER), (255, 255, 255, 0))
    image.putalpha(mask.resize((MASTER, MASTER), Image.LANCZOS))
    image.alpha_composite(logo, ((MASTER - logo.width) // 2, (MASTER - logo.height) // 2))
    return image


def main() -> int:
    master = tile(Image.open(source_logo()))
    ICON_DIR.mkdir(exist_ok=True)
    images = []
    for size, path in zip(ICON_SIZES, icon_files()):
        image = master.resize((size, size), Image.LANCZOS)
        image.save(path, optimize=True)
        images.append(image)
    ico = ICON_DIR / 'varians_synchro.ico'
    images[-1].save(ico, sizes=[(s, s) for s in ICON_SIZES], append_images=images[:-1])
    for path in icon_files() + [ico]:
        print(path.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
