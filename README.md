# belivemethode.com

Site vitrine de BELIVE. Page unique, statique, sans dépendance : aucun framework,
aucune librairie, aucun script de build. Tout le HTML, le CSS et le JavaScript
tiennent dans `index.html`.

Publié sur [belivemethode.com](https://belivemethode.com) via GitHub Pages.

## Aperçu en local

Ouvrir `index.html` dans un navigateur suffit. Pour un rendu identique à la
production (chemins absolus, polices), servir le dossier :

```bash
python3 -m http.server 4322
```

Puis http://localhost:4322

## Structure

```
index.html              La page complète : contenu, styles, scripts, JSON-LD
cgv.html                Conditions générales de vente
confidentialite.html    Politique de confidentialité (RGPD)
mentions-legales.html   Mentions légales
404.html                Page d'erreur servie par GitHub Pages, chemins absolus
CNAME                   Domaine personnalisé lu par GitHub Pages
robots.txt              Indexation ouverte, pointe vers le sitemap
sitemap.xml             Une seule URL : la page d'accueil
assets/
  legal.css             Feuille de style commune aux trois pages légales
  fonts/Outfit.woff2    Police variable 100-900, sous-ensemble latin (35 Ko)
  img/                  Photos en AVIF / WebP / JPEG, favicons, image de partage
  gen_brand.py          Regénère favicons et og.jpg depuis le logotype
  gen_photos.py         Regénère les déclinaisons AVIF / WebP / JPEG des photos
```

Les pages légales et la page 404 portent `noindex` : seule la page d'accueil
est indexable.

## Points techniques

- **Mise en page** : la page d'accueil est la conversion de la maquette Claude
  Design. Chaque bloc porte son style en ligne ; la feuille `<style>` ne tient
  que la fonte, les animations, les survols, la navigation et les ajustements
  mobiles (d'où ses `!important`, seuls capables de passer devant un style en ligne).
- **Animations** : tout est en JavaScript natif, en bas de `index.html`. Le souffle
  de la page (classe `exhale` sur `<html>`, toutes les cinq secondes), l'exercice
  de respiration cohérente, et les effets liés au défilement, pilotés par des
  attributs `data-*` (`data-reveal`, `data-words`, `data-hz`, `data-stack`...).
  Avec « réduire les animations » actif dans le système, rien ne bouge et tout
  le contenu reste lisible.
- **Images** : chaque photo existe en AVIF, WebP et JPEG, en deux largeurs,
  servies par `<picture>`. Les fichiers sources en pleine définition restent dans
  `assets/img/` même s'ils ne sont pas appelés par le HTML : ce sont eux qui
  servent à régénérer les déclinaisons.

## Régénérer les images

Les deux scripts demandent `pillow` et `fonttools` :

```bash
python3 assets/gen_brand.py
```

```bash
python3 assets/gen_photos.py
```

`gen_brand.py` redessine le wordmark avec les mêmes coordonnées que le SVG inclus
dans le site : en cas de modification du logotype, mettre les deux à jour.

## Déploiement

Toute modification poussée sur `main` est mise en ligne automatiquement par
GitHub Pages, en une à deux minutes. Le fichier `CNAME` doit rester à la racine :
c'est lui qui attache le domaine.

## Droits

Contenus, textes, photographies et logotype BELIVE : tous droits réservés.
Le code de ce dépôt est public pour les besoins de l'hébergement, il n'est pas
placé sous licence libre.
