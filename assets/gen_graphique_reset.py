"""Le graphique des piliers de la page /reset/, calculé depuis protocole.py.

    python3 assets/gen_graphique_reset.py /Volumes/T7/PRO/BELIVE/Accompagnement/RESET/Fabrication/protocole.py

Lit journee(w) pour les 13 semaines, range chaque geste dans son pilier, compte
les minutes par jour et réécrit le bloc entre <!-- graphique:debut --> et
<!-- graphique:fin --> dans reset/index.html : une colonne par semaine.
Le détail des gestes reste dans les documents clients, pas sur le site.

La convention est celle de la carte de RESET : la lumière, le froid, le café,
les repas, le téléphone et les pas ne comptent pas, ils se glissent dans des
gestes déjà faits ; le HIIT et le stretching non plus, ils s'ajoutent trois
fois par semaine. Une fourchette (« 4 à 15 min ») compte pour son milieu.
Un geste que le script ne connaît pas l'arrête : il faut alors lui dire à
quel pilier il appartient, dans RANGEMENT ci-dessous.
"""
import html
import importlib.util
import pathlib
import re
import sys

PAGE = pathlib.Path(__file__).resolve().parent.parent / 'reset' / 'index.html'

# Les piliers dans l'ordre de la pile, du bas vers le haut. La nutrition ne prend
# pas de minutes : elle n'a pas de bande. Le relevé n'est pas un pilier, il reste gris.
SERIES = [('SO', 'Sommeil'), ('MO', 'Mouvement'), ('RE', 'Respiration'), ('ME', 'Méditation'), ('RL', 'Ton relevé')]

# Début du libellé dans journee(w) -> pilier, ou None quand le geste ne compte pas.
RANGEMENT = [
    ('Respirations, bord du lit', 'RE'), ('Respiration de midi', 'RE'),
    ('Assise', 'ME'), ('Vision board', 'ME'),
    ('Séquence', 'MO'), ('Marche lente', 'MO'),
    ('Jambes au mur', 'SO'),
    ('Ton relevé', 'RL'),
    ('Lumière', None), ('Douche', None), ('Café', None), ('Repas', None),
    ('Téléphone', None), ('Tes pas', None),
]
MAX = 70          # haut de l'échelle, en minutes
GRILLE = [(0, ''), (30, '30 min'), (60, '1 h')]


def charger(chemin):
    spec = importlib.util.spec_from_file_location('protocole', chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def minutes(duree):
    n = [float(x.replace(',', '.')) for x in re.findall(r'\d+(?:[.,]\d+)?', duree)]
    if not n:
        raise SystemExit(f'Durée sans minutes : « {duree} »')
    return sum(n) / len(n)


def pilier(nom):
    for debut, p in RANGEMENT:
        if nom.startswith(debut):
            return p
    raise SystemExit(f'Geste inconnu dans journee(w) : « {nom} ». Range-le dans RANGEMENT.')


def fr(v):
    return (f'{v:.1f}'.rstrip('0').rstrip('.')).replace('.', ',')


def arrondi(v):
    return round(v) if v < 10 else int(5 * round(v / 5))


def semaines(proto):
    out = []
    for w in range(1, 14):
        matin, midi, soir, _semaine = proto.journee(w)
        v = {c: 0.0 for c, _ in SERIES}
        for nom, duree in matin + midi + soir:
            p = pilier(nom)
            if p:
                v[p] += minutes(duree)
        out.append(v)
    return out


def rendu(proto):
    data = semaines(proto)
    noms = dict(SERIES)
    phases, avant = [], None
    for k, ph in proto.PHASES.items():
        a, b = ph['weeks']
        sems = []
        for w in range(a, b + 1):
            v = data[w - 1]
            total = sum(v.values())
            titre = proto.WEEKS[w]['titre']
            change = avant is None or abs(total - avant) > 0.01
            avant = total
            segs = [(c, v[c]) for c, _ in SERIES if v[c] > 0]
            detail = ', '.join(f'{noms[c].lower()} {fr(m)}' for c, m in sorted(segs, key=lambda x: -x[1]))
            entre = titre[0].lower() + titre[1:]
            aria = f'Semaine {w}, {entre} : {fr(total)} min par jour. {detail[0].upper() + detail[1:]}.'
            h = [f'          <li class="sem" tabindex="0" data-sem="{w}" data-titre="{html.escape(titre)}" '
                 f'data-total="{fr(total)}" data-detail="{html.escape(detail)}" aria-label="{html.escape(aria)}" '
                 f'style="--s:{w};--t:{total:g};--k:{len(segs)}">']
            # toujours présent, vide quand rien ne change : sur téléphone, toutes les barres gardent la même échelle
            h.append(f'            <span class="sem__total" aria-hidden="true">{str(arrondi(total)) + " min" if change else ""}</span>')
            h.append('            <span class="sem__plot" aria-hidden="true">')
            for i, (c, m) in enumerate(segs):
                h.append(f'              <i class="seg" data-p="{c}" style="--v:{m:g};--c:var(--c-{c.lower()})"></i>')
            h.append('            </span>')
            h.append(f'            <span class="sem__n" aria-hidden="true">S{w}</span>')
            h.append(f'            <span class="sem__entre" aria-hidden="true">{"+ " + html.escape(entre) if change else ""}</span>')
            h.append('          </li>')
            sems.append('\n'.join(h))
        phases.append(
            f'        <div class="phase-b" style="--n:{b - a + 1}">\n'
            f'          <p class="phase-b__nom"><b>{ph["rom"]}</b> {html.escape(ph["name"])}</p>\n'
            f'          <ol class="phase-b__sems">\n' + '\n'.join(sems) + '\n          </ol>\n        </div>')

    legende = '\n'.join(
        f'        <li data-p="{c}" tabindex="0"><i style="--c:var(--c-{c.lower()})"></i>{html.escape(n)}</li>'
        for c, n in SERIES)
    grille = '\n'.join(f'        <span style="--g:{g}"><b>{t}</b></span>' for g, t in GRILLE)
    debut = data[0]
    return f'''    <!-- graphique:debut · généré par assets/gen_graphique_reset.py depuis protocole.py, ne pas éditer à la main -->
    <figure class="barres" data-barres style="--max:{MAX}">
      <div class="barres__tete">
        <p class="courbe__lecture" aria-live="polite"><b data-lec-sem>De {fr(sum(debut.values()))} min à environ 1 h</b><span data-lec-min>par jour, en 8 semaines. Choisis une semaine pour le détail.</span></p>
        <ul class="barres__legende" aria-label="Légende">
{legende}
        </ul>
      </div>
      <div class="barres__zone">
        <div class="barres__grille" aria-hidden="true">
{grille}
        </div>
        <div class="barres__phases">
{chr(10).join(phases)}
        </div>
      </div>
      <figcaption>Chaque colonne est une semaine&nbsp;; sa hauteur, le temps par jour. La lumière, le froid, le café et les repas n'y sont pas&nbsp;: ils se glissent dans des gestes que tu fais déjà. Le HIIT et le stretching s'ajoutent 3 fois par semaine, 20 à 30&nbsp;min.</figcaption>
    </figure>
    <!-- graphique:fin -->'''


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    bloc = rendu(charger(sys.argv[1]))
    page = PAGE.read_text(encoding='utf-8')
    a = page.index('    <!-- graphique:debut')
    b = page.index('<!-- graphique:fin -->') + len('<!-- graphique:fin -->')
    PAGE.write_text(page[:a] + bloc + page[b:], encoding='utf-8')
    print(f'{PAGE.relative_to(PAGE.parent.parent)} : graphique réécrit')


if __name__ == '__main__':
    main()
