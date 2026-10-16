"""Génère les trois planches au trait de la page RESET (SVG + positions des légendes)."""
import math, random, json, sys
out = {}

def smooth(e0, e1, x):
    t = max(0., min(1., (x - e0)/(e1 - e0))); return t*t*(3 - 2*t)

# ---------- Fig. 01 : l'onde du souffle ----------
W, H, cy = 1000, 150, 75
x0, x1 = 20, 980
def trace(k):
    pts = []; ph = 0.; prev = None
    for i in range(0, 2001):
        u = i/2000; x = x0 + u*(x1 - x0)
        s = smooth(.08, .92, u)
        f = (30*(1 - s) + 2.4*s)*k                   # cycles sur toute la largeur
        a = 8*(1 - s) + 58*s
        a *= 1 + .55*(1 - s)*math.sin(u*41)*math.sin(u*17 + 1)   # le souffle court est irrégulier
        a *= smooth(0, .015, u)
        if prev is not None: ph += 2*math.pi*f*(u - prev)
        prev = u
        pts.append((x, cy - a*math.sin(ph)))
    return pts, ph
_, ph = trace(1)
k = (round(ph/math.pi))*math.pi/ph               # finir pile sur l'axe
pts, _ = trace(k)
pts = pts[::4]
d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts)
ticks = ''.join('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>' % (x0 + u*(x1-x0), cy - 4, x0 + u*(x1-x0), cy + 4) for u in [i/40 for i in range(41)])
out['onde'] = {'d': d, 'ticks': ticks}

# ---------- Fig. 02 : la course du jour ----------
W2, H2 = 480, 300; cx, hy, R = 240, 200, 168
def P(a, r=R): return (cx + r*math.cos(math.radians(a)), hy - r*math.sin(math.radians(a)))
arc = 'M%.1f %.1f A%d %d 0 0 1 %.1f %.1f' % (*P(180), R, R, *P(0))
nuit = 'M%.1f %.1f A%d %d 0 0 0 %.1f %.1f' % (*P(0), R, R, *P(-34))
gr = ''
for a in range(0, 181, 10):
    l = 9 if a % 30 == 0 else 5
    (xa, ya), (xb, yb) = P(a, R + 4), P(a, R + 4 + l)
    gr += '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (xa, ya, xb, yb)
moments = [('lever', 172), ('midi', 90), ('soiree', 38), ('coucher', -24)]
mpos = {k: P(a) for k, a in moments}
# la mer de nuages, au trait : une ligne de dômes posée sous l'horizon
random.seed(7)
def domes(y, x, xe, rmin, rmax):
    s = 'M%.1f %.1f' % (x, y)
    while x < xe:
        r = random.uniform(rmin, rmax); r = min(r, (xe - x)/2) if xe - x > 2 else r
        if xe - x < 4: break
        s += ' A%.1f %.1f 0 0 1 %.1f %.1f' % (r, r*.82, x + 2*r, y); x += 2*r
    return s
n1 = domes(hy + 22, 26, 454, 10, 30)
n2 = domes(hy + 58, 70, 410, 14, 34)
n3 = ''
out['jour'] = {'arc': arc, 'nuit': nuit, 'gr': gr, 'm': {k: [round(v[0], 1), round(v[1], 1)] for k, v in mpos.items()},
               'n1': n1, 'n2': n2, 'n3': n3, 'hy': hy, 'W': W2, 'H': H2}

# ---------- Fig. 03 : l'arbre-poumon ----------
random.seed(11)
W3, H3 = 440, 470
base = (220, 330)
segs = []      # (x1, y1, x2, y2, niveau)
tips = []
def branche(x, y, ang, L, lev, maxlev, crown):
    a = math.radians(ang)
    x2, y2 = x + L*math.sin(a), y - L*math.cos(a)
    segs.append((x, y, x2, y2, lev)); crown.append((x2, y2))
    if lev >= maxlev:
        tips.append((x2, y2, lev)); return
    spread = 24 + random.uniform(-4, 5)
    for sgn in (-1, 1):
        branche(x2, y2, ang + sgn*spread + random.uniform(-5, 5), L*random.uniform(.66, .74), lev + 1, maxlev, crown)
# le tronc : la trachée
TRONC = 410
segs.append((base[0], TRONC, base[0], base[1], 0))
mains = [('NU', -58, 92, 4), ('MO', -22, 118, 4), ('RE', 8, 104, 4), ('ME', 44, 96, 4)]
labels = {}
for code, ang, L, ml in mains:
    crown = []
    branche(base[0], base[1], ang, L, 1, ml, crown)
    a = math.radians(ang); fx, fy = crown[0]
    labels[code] = [round(fx + .42*L*math.sin(a), 1), round(fy - .42*L*math.cos(a), 1)]
# les racines : le sommeil
roots = []
random.seed(5)
def racine(x, y, ang, L, lev):
    a = math.radians(ang); x2, y2 = x + L*math.sin(a), y + L*math.cos(a)
    roots.append((x, y, x2, y2, lev))
    if lev < 3:
        for sgn in (-1, 1): racine(x2, y2, ang + sgn*(26 + random.uniform(-6, 6)), L*.62, lev + 1)
for ang, L in [(-62, 46), (-24, 40), (22, 42), (60, 48)]:
    racine(base[0], TRONC, ang, L, 1)
allx = [v for sg in segs + roots for v in (sg[0], sg[2])]; ally = [v for sg in segs + roots for v in (sg[1], sg[3])]
mx, my = 18, 18
vb = [min(allx) - mx, min(ally) - mx, max(allx) - min(allx) + 2*mx, max(ally) - min(ally) + 2*my + 26]
labels['SO'] = [base[0], max(ally) + 22]
W3, H3 = vb[2], vb[3]
sw = {0: 5.5, 1: 3.4, 2: 2.3, 3: 1.6, 4: 1.15}
def q(v): return '%.1f' % v
tree = ''
for lev in sorted(sw):
    ds = ' '.join('M%s %sL%s %s' % (q(a), q(b), q(c), q(e)) for a, b, c, e, l in segs if l == lev)
    if ds: tree += '<path d="%s" stroke-width="%s"/>' % (ds, sw[lev])
rds = ' '.join('M%s %sL%s %s' % (q(a), q(b), q(c), q(e)) for a, b, c, e, l in roots)
tips_s = ''.join('<circle cx="%s" cy="%s" r="%s"/>' % (q(x), q(y), '3.6' if l >= 4 else '4.4') for x, y, l in tips)
out['arbre'] = {'tree': tree, 'roots': rds, 'tips': tips_s, 'labels': labels, 'vb': [round(v, 1) for v in vb]}
json.dump(out, open(sys.argv[1], 'w'))
print('onde', len(d), 'arbre', len(tree), 'pointes', len(tips))
