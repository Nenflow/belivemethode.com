"""Décline les deux photos en WebP (et AVIF si disponible) sur deux largeurs."""
import os
from PIL import Image, features

IMG = "/Volumes/T7/PRO/Claude Code/Site web V2/assets/img"
HAS_AVIF = features.check("avif")

JOBS = [
    ("tristan-accompagnement.jpg", [600, 900]),
    ("seance-groupe-2.jpg", [800, 1400]),
]

print(f"AVIF disponible : {HAS_AVIF}")
for name, widths in JOBS:
    src = Image.open(os.path.join(IMG, name)).convert("RGB")
    stem = name.rsplit(".", 1)[0]
    for w in widths:
        h = round(src.height * w / src.width)
        im = src.resize((w, h), Image.LANCZOS)
        out = []
        p = os.path.join(IMG, f"{stem}-{w}.jpg")
        im.save(p, quality=82, optimize=True, progressive=True)
        out.append(p)
        p = os.path.join(IMG, f"{stem}-{w}.webp")
        im.save(p, quality=78, method=6)
        out.append(p)
        if HAS_AVIF:
            p = os.path.join(IMG, f"{stem}-{w}.avif")
            im.save(p, quality=55)
            out.append(p)
        print(f"  {stem}-{w}  {w}x{h}  " +
              "  ".join(f"{os.path.basename(f).rsplit('.',1)[1]}:{os.path.getsize(f)/1024:.0f}Ko"
                        for f in out))
    print(f"  (source {name} : {src.width}x{src.height}, "
          f"{os.path.getsize(os.path.join(IMG,name))/1024:.0f} Ko)")
