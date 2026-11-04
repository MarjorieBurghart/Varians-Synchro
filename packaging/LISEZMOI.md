# Version prête à l'emploi de Varians-Synchro

Archives sans Python à installer, pour Windows (x64), macOS (Apple Silicon
et Intel) et Linux (x64), construites par PyInstaller, sur le modèle de
Varians. Ce qu'un utilisateur lit dans l'archive : `readme/` (sept langues).

## Publier

Le workflow **Binaries** (`.github/workflows/binaries.yml`) construit les
quatre archives et les joint à la release **dès qu'elle est publiée**, avec
leur empreinte SHA-256 (`.sha256`). Rien d'autre à faire.

Pour une release déjà publiée : Actions ▸ Binaries ▸ **Run workflow**,
choisir la branche ou le tag à construire, et indiquer la release dans
**tag** (`v0.8.6.0`). Le workflow refuse de joindre des archives dont la
version (`core.VERSION`) n'est pas celle du tag. Sans **tag**, les archives
sont seulement téléchargeables dans le résumé du workflow (pour un essai).

Le workflow tourne aussi, sans rien publier, quand `packaging/` ou le
workflow change.

## Ce qui est vérifié

`packaging/build.py`, sur chaque système :

1. construit avec PyInstaller (`varians_synchro.spec`, point d'entrée
   `run.py`) ;
2. place le dossier sous `Varians-Synchro-<version>/`, avec le LISEZMOI ×7,
   les textes des licences (`licences/`) et une copie du projet d'exemple
   (`demo_local_ALTO/`) pour l'utilisateur ;
3. lance l'exécutable construit : `Varians-Synchro --self-test rapport.json`
   (`varians_synchro/self_test.py`) vérifie les traductions, l'aide, les
   icônes, ouvre et enregistre une copie du projet d'exemple, y fait une
   synchronisation A ↔ B avec ses deux exports vers Varians, et ouvre le
   projet dans la fenêtre. Dans le workflow, la fenêtre s'ouvre avec le
   module d'affichage du système (windows, cocoa, xcb sous Xvfb) ;
4. refuse l'archive si une vérification échoue, si un lien symbolique est
   cassé ou si la vérification a laissé un fichier dans le dossier ;
5. zippe (liens symboliques et droits gardés ; `ditto` sous macOS) et
   écrit l'empreinte.

Le rapport de vérification est gardé dans le résumé du workflow
(`diagnostic-…`), même en cas d'échec.

## Construire sur sa machine

```
pip install -r requirements.txt -r packaging/requirements.txt
python packaging/build.py            # archive dans build/binaries/
```

Sans écran, la vérification utilise `QT_QPA_PLATFORM=offscreen` ; sous
Linux, `QT_QPA_PLATFORM=xcb xvfb-run -a python packaging/build.py` vérifie
aussi l'affichage X11. Sous Linux, installer d'abord les bibliothèques xcb
listées dans le workflow : celles qui sont présentes à la construction sont
emportées dans l'archive.

## Points à connaître

- **Non signé.** Windows (SmartScreen) et macOS (Gatekeeper) avertissent au
  premier lancement ; le LISEZMOI explique comment passer. Signer
  demanderait un certificat Windows et un compte développeur Apple.
- **Données.** Varians-Synchro lit ses fichiers de données à côté de son
  paquet (`Path(__file__).resolve().parent.parent / 'i18n'`…) : la recette
  les place dans `_internal/` sous le même nom (`DATA_FOLDERS`). Un nouveau
  dossier de données doit y être ajouté ; `tests/test_packaging.py` le
  vérifie.
- **Projet d'exemple, deux fois.** `--self-test` vérifie celui des données
  (`_internal/demo_local_ALTO`) : un `Varians-Synchro.app` glissé dans
  Applications se vérifie donc toujours. La copie posée à côté de
  l'exécutable est celle de l'utilisateur (« Premier essai » du guide).
- **Pas de console sous Windows.** `sys.stderr` vaut `None` : `run.py`
  n'active alors pas `faulthandler`, et `--self-test` écrit son rapport
  dans un fichier.
- **Greffons Qt retirés** (`UNUSED_QT`, `UNUSED_LINUX`) : clavier virtuel
  (QML), images PDF, plateformes embarquées, thème et pile GTK. Les greffons
  TLS restent : les vignettes IIIF passent par QtNetwork.
- **Certificats HTTPS** : `rthook_certificates.py` utilise ceux de certifi
  quand ceux du système manquent (macOS, Linux hors Debian/Ubuntu), pour
  les manifestes et images IIIF lus par Python.
- **Linux** : construit sur Ubuntu 22.04, l'archive demande glibc 2.35 ou
  plus récent (Ubuntu 22.04, Debian 12, Fedora 36…). Essai local (Ubuntu
  24.04) : archive de 52 Mo, dossier de 138 Mo, vérification en 6 s.
- **Icône** : `icons/varians_synchro.ico` pour l'exécutable Windows,
  `icons/varians_synchro_256.png` (converti en `.icns` avec Pillow) pour le
  paquet `.app` ; ce sont celles des fenêtres (`app_icon.py`).
- **Licence de Varians-Synchro** : le dépôt n'a pas encore de fichier de
  licence ; seules celles des composants livrés sont dans `licences/`.
