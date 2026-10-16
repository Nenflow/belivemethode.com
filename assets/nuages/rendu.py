"""Calcule les images de nuages du site et les dépose dans assets/img/nuages.

    python3 assets/nuages/rendu.py            tous les réglages qui ont une sortie
    python3 assets/nuages/rendu.py mer        un seul (nom du réglage ou de la sortie)

Le rendu tourne dans Google Chrome sans interface, sur la puce graphique :
gen.html est un lanceur de rayons WebGL (mer de nuages, cumulus, rocher), les
réglages sont dans reglages.json. Chaque image sort en PNG dans rendus/ (ignoré
par Git), puis en AVIF (sips, macOS) et en WebP (Chrome) dans assets/img/nuages.
Les dimensions doivent être paires : un AVIF de hauteur impaire écrit par sips
s'affiche transparent dans Chrome.
"""
import base64, json, os, re, shutil, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SORTIE = os.path.join(ICI, '..', 'img', 'nuages')
RENDUS = os.path.join(ICI, 'rendus')
reglages = json.load(open(os.path.join(ICI, 'reglages.json'), encoding='utf-8'))


def fusion(base, dessus):
    r = json.loads(json.dumps(base))
    for k, v in dessus.items():
        r[k] = fusion(r[k], v) if isinstance(v, dict) and isinstance(r.get(k), dict) else v
    return r


def resoudre(nom):
    p = reglages[nom]
    if 'base' in p:
        p = fusion(resoudre(p['base']), {k: v for k, v in p.items() if k != 'base'})
    return p


def rendre(nom):
    cfg = resoudre(nom)
    assert cfg['w'] % 2 == 0 and cfg['h'] % 2 == 0, nom + ' : dimensions impaires'
    os.makedirs(RENDUS, exist_ok=True)
    profil = os.path.join(RENDUS, 'profil-' + nom)
    adresse = 'file://' + os.path.join(ICI, 'gen.html') + '?c=' + base64.b64encode(json.dumps(cfg).encode()).decode()
    page = subprocess.run([CHROME, '--headless=new', '--user-data-dir=' + profil, '--no-first-run',
                           '--virtual-time-budget=120000', '--dump-dom', adresse],
                          capture_output=True, text=True, timeout=300).stdout
    subprocess.run(['pkill', '-f', profil])
    shutil.rmtree(profil, ignore_errors=True)
    journal = re.search(r'<pre id="log">([^<]*)', page)
    print(nom, ':', journal.group(1) if journal else 'pas de réponse')
    images = {}
    for sorte in ('png', 'webp'):
        m = re.search(r'<pre id="%s">data:image/%s;base64,([^<]*)' % (sorte, sorte), page)
        if not m:
            sys.exit(nom + ' : rendu ' + sorte + ' manquant')
        images[sorte] = os.path.join(RENDUS, nom + '.' + sorte)
        open(images[sorte], 'wb').write(base64.b64decode(m.group(1)))
    if cfg.get('sortie'):
        cible = os.path.join(SORTIE, cfg['sortie'])
        subprocess.run(['sips', '-s', 'format', 'avif', '-s', 'formatOptions', str(cfg.get('avif', 70)),
                        images['png'], '--out', cible + '.avif'], check=True, stdout=subprocess.DEVNULL)
        shutil.copy(images['webp'], cible + '.webp')
        print('   ->', os.path.relpath(cible, os.path.join(ICI, '..', '..')) + '.avif / .webp')


demandes = sys.argv[1:] or [n for n, p in reglages.items() if p.get('sortie')]
for d in demandes:
    noms = [n for n, p in reglages.items() if n == d or p.get('sortie') == d]
    if not noms:
        sys.exit('réglage inconnu : ' + d)
    for n in noms:
        rendre(n)
