"""Met l'espace RESET à jour depuis protocole.py, et y recopie les PDF client.

    python3 assets/gen_espace.py CHEMIN/protocole.py ["CHEMIN/Documents clients"]

protocole.py est la source unique de RESET : ce script le lit, il ne le modifie
jamais. Il réécrit le bloc compris entre les deux marqueurs de espace/index.html
(PHASES, SEMAINES, OPEN, BW, CO2, RESPIRATIONS_MIDI, DOCS). Le reste de la page
ne se touche pas.

Avec le dossier des documents client en second argument, il recopie aussi chaque
PDF de DOCUMENTS dans espace/docs/, sous son nom stable : il prend la version la
plus haute de chaque titre (« RESET · Le HIIT · v3.pdf » passe devant la v2) et
l'écrit par-dessus l'ancienne. L'adresse du document ne change jamais.

Python seul, sans dépendance.
"""
import importlib.util, json, os, re, shutil, sys, unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(RACINE, 'espace', 'index.html')
DOSSIER_DOCS = os.path.join(RACINE, 'espace', 'docs')
DEBUT, FIN = '/* <protocole> */', '/* </protocole> */'

# Les documents de l'espace, dans l'ordre d'affichage.
#   titre   : le nom affiché dans l'espace.
#   fichier : le nom en ligne, dans espace/docs/. Ne jamais le changer : c'est l'adresse.
#   source  : le titre dans « Documents clients », sans « RESET · » ni la version.
#   des     : la semaine où il s'ouvre, 0 = dès l'inscription.
#   note    : pour un document qui ne va jamais en ligne, la phrase affichée à sa place.
# Ton vision board est un guide vendu, et l'espace est public pour qui connaît
# l'adresse : il n'a pas de fichier, et ce script refuse de le copier.
DOCUMENTS = [
    dict(titre='Ta sécurité',                    fichier='ta-securite.pdf',                    source='Ta sécurité',                    des=0),
    dict(titre='La carte de RESET',              fichier='la-carte-de-reset.pdf',              source='La carte de RESET',              des=1),
    dict(titre='Phase I · Rencontre Intérieure', fichier='phase-1-rencontre-interieure.pdf',   source='Phase I · Rencontre Intérieure', des=1),
    dict(titre='Ton journal, à imprimer',        fichier='ton-journal.pdf',                    source='Ton journal',                    des=1),
    dict(titre='Tes respirations',               fichier='tes-respirations.pdf',               source='Tes respirations',               des=1),
    dict(titre='Le test CO2',                    fichier='le-test-co2.pdf',                    source='Le test CO2',                    des=1),
    dict(titre='Le mouvement du matin',          fichier='le-mouvement-du-matin.pdf',          source='Le mouvement du matin',          des=4),
    dict(titre='Phase II · La Traversée',        fichier='phase-2-la-traversee.pdf',           source='Phase II · La Traversée',        des=5),
    dict(titre='Le HIIT',                        fichier='le-hiit.pdf',                        source='Le HIIT',                        des=5),
    dict(titre='Le stretching',                  fichier='le-stretching.pdf',                  source='Le stretching',                  des=6),
    dict(titre='Phase III · La Reconstruction',  fichier='phase-3-la-reconstruction.pdf',      source='Phase III · La Reconstruction',  des=8),
    dict(titre='Ton vision board',               fichier=None,                                 source=None,                             des=8,
         note='Remis en call, semaine 8.'),
    dict(titre="Phase IV · L'Intégration",       fichier='phase-4-l-integration.pdf',          source="Phase IV · L'Intégration",       des=11),
    dict(titre='Mon protocole',                  fichier='mon-protocole.pdf',                  source='Mon protocole',                  des=11),
]
JAMAIS_EN_LIGNE = 'vision board'


def sortir(msg):
    sys.exit('gen_espace : ' + msg)


def norme(t):
    """Les noms de fichier d'un disque externe arrivent parfois décomposés (é = e + ´)."""
    return unicodedata.normalize('NFC', t).replace('’', "'")


def charger(chemin):
    sys.dont_write_bytecode = True          # pas de __pycache__ à côté de protocole.py
    spec = importlib.util.spec_from_file_location('protocole', chemin)
    if spec is None:
        sortir("impossible de lire " + chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pages(chemin):
    """Nombre de pages d'un PDF, sans bibliothèque : on compte ses objets /Page."""
    n = len(re.findall(rb'/Type\s*/Page(?![a-zA-Z])', open(chemin, 'rb').read()))
    return n or None


def balises(x, ou=''):
    """Le texte de protocole.py peut porter du gras (<b>), rien d'autre."""
    if isinstance(x, str):
        for b in re.findall(r'<[^>]*>', x):
            if b not in ('<b>', '</b>'):
                sortir('balise %s refusée dans %s : « %s »' % (b, ou, x))
    elif isinstance(x, dict):
        for k, v in x.items(): balises(v, ou)
    elif isinstance(x, (list, tuple)):
        for v in x: balises(v, ou)


def donnees(p):
    phases = []
    for n, d in sorted(p.PHASES.items()):
        phases.append(dict(n=n, rom=d['rom'], name=d['name'], verb=d['verb'], weeks=list(d['weeks']),
                           intent=d['intent'], court=d['court'], tags=list(d['tags']),
                           continue_=list(d.get('continue_', [])), apres=list(d.get('apres', []))))
    semaines = {}
    for w in range(1, 14):
        matin, midi, soir, semaine = p.journee(w)
        semaines[w] = dict(titre=p.WEEKS[w]['titre'], journal=list(p.WEEKS[w]['journal']),
                           journee=dict(matin=[list(x) for x in matin], midi=[list(x) for x in midi],
                                        soir=[list(x) for x in soir], semaine=[list(x) for x in semaine]),
                           rdv=p.rdv(w, 'carte'))
    respirations = [dict(etat=e, nom=nom, geste=g, duree=d + ' ' + u) for e, nom, g, d, u in p.RESPIRATIONS_MIDI]
    return phases, semaines, sorted(p.OPEN), dict(sorted(p.BW.items())), dict(sorted(p.CO2.items())), respirations


def copier(dossier):
    """Recopie la dernière version de chaque document dans espace/docs/."""
    os.makedirs(DOSSIER_DOCS, exist_ok=True)
    noms = {norme(f): f for f in os.listdir(dossier) if f.lower().endswith('.pdf') and not f.startswith('._')}
    pris = set()
    for d in DOCUMENTS:
        if not d['fichier']:
            continue
        motif = re.compile(r'^RESET · ' + re.escape(norme(d['source'])) + r' · v(\d+)( \(à imprimer\))?\.pdf$')
        versions = sorted(((int(m.group(1)), f) for f in noms for m in [motif.match(f)] if m), reverse=True)
        if not versions:
            print('  introuvable :', d['source'])
            continue
        v, f = versions[0]
        if JAMAIS_EN_LIGNE in f.lower():
            sortir('refus de copier ' + f)
        pris.update(x for _, x in versions)
        src, dst = os.path.join(dossier, noms[f]), os.path.join(DOSSIER_DOCS, d['fichier'])
        neuf = open(src, 'rb').read()
        if not os.path.exists(dst) or open(dst, 'rb').read() != neuf:
            shutil.copyfile(src, dst)
            print('  copié   : %s  ←  %s' % (d['fichier'], f))
        else:
            print('  à jour  : %s  (v%d)' % (d['fichier'], v))
    for f in sorted(set(noms) - pris):
        if JAMAIS_EN_LIGNE not in f.lower():
            print('  pas dans l\'espace :', f)


def docs():
    out = []
    for d in DOCUMENTS:
        e = dict(titre=d['titre'], des=d['des'])
        if d['fichier']:
            chemin = os.path.join(DOSSIER_DOCS, d['fichier'])
            e['fichier'] = d['fichier']
            e['pages'] = pages(chemin) if os.path.exists(chemin) else None
            if not os.path.exists(chemin):
                print('  manquant dans espace/docs/ :', d['fichier'])
        else:
            e['note'] = d['note']
        out.append(e)
    attendus = {d['fichier'] for d in DOCUMENTS if d['fichier']}
    if os.path.isdir(DOSSIER_DOCS):
        for f in sorted(os.listdir(DOSSIER_DOCS)):
            if f.endswith('.pdf') and f not in attendus:
                print('  en trop dans espace/docs/ (laissé tel quel) :', f)
    return out


def j(x):
    # « </ » fermerait la balise <script> : on l'écrit « <\/ », identique pour JavaScript.
    return json.dumps(x, ensure_ascii=False).replace('</', '<\\/')


def bloc(phases, semaines, ouv, bw, co2, resp, documents):
    L = [DEBUT,
         '/* Écrit par assets/gen_espace.py depuis protocole.py. Ne se modifie pas à la main :',
         '   on change protocole.py, puis on relance le script. */',
         'const RESET = {',
         '  PHASES: [']
    L += ['    ' + j(p) + ',' for p in phases]
    L += ['  ],', '  SEMAINES: {']
    L += ['    %d: %s,' % (w, j(s)) for w, s in semaines.items()]
    L += ['  },',
          '  OPEN: %s,' % j(ouv),
          '  BW: %s,' % j(bw),
          '  CO2: %s,' % j(co2),
          '  RESPIRATIONS_MIDI: [']
    L += ['    ' + j(r) + ',' for r in resp]
    L += ['  ],', '  DOCS: [']
    L += ['    ' + j(d) + ',' for d in documents]
    L += ['  ]', '};', FIN]
    return '\n'.join(L)


def main():
    if len(sys.argv) not in (2, 3):
        sortir(__doc__.strip().splitlines()[2].strip())
    proto = charger(sys.argv[1])
    if len(sys.argv) == 3:
        print('Documents :')
        copier(sys.argv[2])
    data = donnees(proto)
    balises(data, 'protocole.py')
    texte = open(PAGE, encoding='utf-8').read()
    if texte.count(DEBUT) != 1 or texte.count(FIN) != 1:
        sortir('les marqueurs %s et %s doivent être une fois chacun dans %s' % (DEBUT, FIN, PAGE))
    a, b = texte.index(DEBUT), texte.index(FIN) + len(FIN)
    neuf = texte[:a] + bloc(*data, docs()) + texte[b:]
    if neuf != texte:
        open(PAGE, 'w', encoding='utf-8').write(neuf)
        print('espace/index.html mis à jour.')
    else:
        print('espace/index.html déjà à jour.')


if __name__ == '__main__':
    main()
