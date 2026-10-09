"""Génère les assets de marque BELIVE : favicons PNG + image de partage (Open Graph).

Les icônes sont tirées du logo `logo-b.png` (le « B » et sa pastille sur fond nuit).
Le wordmark de l'image de partage est redessiné ici avec les mêmes coordonnées que
le SVG du site (grille : hauteur de capitale = 100, épaisseur de trait = 5).
"""
import io, math, os
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

SITE = "/Volumes/T7/PRO/Claude Code/Site web V2"
IMG = os.path.join(SITE, "assets/img")
LOGO = os.path.join(IMG, "logo-b.png")  # 800 × 800, source des icônes
SS = 4  # supersampling

INK = (18, 23, 27)
PAGE = (223, 228, 232)
ICE = (143, 192, 218)
ON_DARK = (238, 243, 246)
INK2 = (92, 104, 115)


def wordmark_paths(dot=True):
    """Segments (lignes) et arcs du logotype, en unités de la grille."""
    lines = [
        (0, 0, 0, 100),          # B — montant
        (0, 0, 40, 0), (40, 50, 0, 50),
        (0, 50, 40, 50), (40, 100, 0, 100),
        (135, 0, 197, 0), (135, 50, 197, 50), (135, 100, 197, 100),   # E
        (267, 0, 267, 100), (267, 100, 322, 100),                     # L
        (392, 0, 392, 100),                                           # I
        (462, 0, 495, 100), (495, 100, 528, 0),                       # V
        (598, 0, 660, 0), (598, 50, 660, 50), (598, 100, 660, 100),   # E
    ]
    arcs = [(40, 25, 25, -90, 90), (40, 75, 25, -90, 90)]  # cx, cy, r, deg0, deg1
    circle = (736, 97, 6) if dot else None
    return lines, arcs, circle


def draw_wordmark(d, ox, oy, scale, color, stroke=5, dot=True, dot_color=None):
    lines, arcs, circle = wordmark_paths(dot)
    w = max(1, round(stroke * scale))
    for x1, y1, x2, y2 in lines:
        d.line([ox + x1 * scale, oy + y1 * scale, ox + x2 * scale, oy + y2 * scale],
               fill=color, width=w)
    for cx, cy, r, a0, a1 in arcs:
        # PIL épaissit l'arc vers l'intérieur : on dilate la boîte d'un demi-trait
        # pour que la ligne médiane de l'arc tombe bien sur le rayon r.
        e = w / 2
        box = [ox + (cx - r) * scale - e, oy + (cy - r) * scale - e,
               ox + (cx + r) * scale + e, oy + (cy + r) * scale + e]
        d.arc(box, a0, a1, fill=color, width=w)
    if circle:
        cx, cy, r = circle
        d.ellipse([ox + (cx - r) * scale, oy + (cy - r) * scale,
                   ox + (cx + r) * scale, oy + (cy + r) * scale],
                  fill=dot_color or color)


def logo_icon(size, side, rounded=True):
    """Icône tirée du logo : un carré de `side` px centré sur le B et sa pastille.

    Plus le carré est serré, plus le B reste lisible en petit : 530 pour l'onglet
    du navigateur, 640 pour l'écran d'accueil, qui garde les orbites entières.
    """
    cx, cy = 414, 398  # centre du B et de sa pastille dans la source
    h = side / 2
    im = Image.open(LOGO).convert("RGB")
    im = im.resize((size, size), Image.LANCZOS, box=(cx - h, cy - h, cx + h, cy + h))
    if rounded:
        S = size * SS
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=S * 0.22, fill=255)
        im.putalpha(mask.resize((size, size), Image.LANCZOS))
    return im


def load_font(px, weight=400):
    ttf = "/tmp/outfit-static.ttf"
    if not os.path.exists(ttf):
        f = TTFont(os.path.join(SITE, "assets/fonts/Outfit.woff2"))
        f.flavor = None
        f.save(ttf)
    fnt = ImageFont.truetype(ttf, px)
    try:
        fnt.set_variation_by_axes([weight])
    except Exception:
        pass
    return fnt


def og_image():
    W, H = 1200, 630
    S = (W * 2, H * 2)
    im = Image.new("RGB", S, PAGE)

    # halo glacier diffus, en haut à droite
    glow = Image.new("L", S, 0)
    gd = ImageDraw.Draw(glow)
    for i in range(60):
        t = i / 60
        r = int(S[0] * 0.75 * (1 - t) ** 0.6)
        gd.ellipse([S[0] * 0.72 - r, S[1] * 0.18 - r, S[0] * 0.72 + r, S[1] * 0.18 + r],
                   fill=int(255 * t * 0.6))
    im = Image.composite(Image.new("RGB", S, (232, 241, 247)), im, glow)

    d = ImageDraw.Draw(im)
    scale = (W * 0.58 * 2) / 742
    wm_w, wm_h = 742 * scale, 106 * scale
    ox = (S[0] - wm_w) / 2
    oy = S[1] * 0.36 - wm_h / 2
    draw_wordmark(d, ox, oy, scale, INK, stroke=5, dot=True, dot_color=ICE)

    f1 = load_font(46, 500)
    f2 = load_font(32, 400)
    t1 = "Breathwork · Système nerveux · Naturopathie"
    t2 = "Sortir du pilote automatique, en commençant par le corps."
    for txt, fnt, y, col in ((t1, f1, 0.60, INK), (t2, f2, 0.70, INK2)):
        bb = d.textbbox((0, 0), txt, font=fnt)
        d.text(((S[0] - (bb[2] - bb[0])) / 2, S[1] * y), txt, font=fnt, fill=col)

    return im.resize((W, H), Image.LANCZOS)


os.makedirs(IMG, exist_ok=True)
logo_icon(32, 530).save(os.path.join(IMG, "favicon-32.png"), optimize=True)
logo_icon(192, 530).save(os.path.join(IMG, "favicon-192.png"), optimize=True)
# iOS arrondit lui-même les coins : pleine surface, sans transparence
logo_icon(180, 640, rounded=False).save(os.path.join(IMG, "apple-touch-icon.png"), optimize=True)
og_image().save(os.path.join(IMG, "og.jpg"), quality=88, optimize=True, progressive=True)
print("ok")
for n in ("favicon-32.png", "favicon-192.png", "apple-touch-icon.png", "og.jpg"):
    p = os.path.join(IMG, n)
    print(f"  {n:24} {os.path.getsize(p)/1024:6.1f} Ko")
