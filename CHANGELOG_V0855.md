# Varians-Synchro V0.8.5.5 — Refonte des traductions

Base : archive officielle v0.8.5.4 transmise par l'utilisatrice.

## Modifications

- Cinq catalogues XML (`de`, `cs`, `it`, `ru`, `ja`) : traduction de **244 chaînes chacun**, pour **1 220 chaînes** nouvellement localisées ; 653 clés par langue.
- Conservation stricte des clés, paramètres `{...}`, éléments TEI `<lb/>`, balises HTML des libellés et identifiants techniques (`ALTO`, `PAGE`, `IIIF`, `base_keys`, `validated/`, `working/`).
- Actualisation des guides, de l'index documentaire, de la version applicative, du rapport de couverture et des empreintes SHA-256.
- Retrait des cinq listes obsolètes `i18n/FALLBACK_*.txt` ; liste historique unique des clés complétées dans `docs/i18n_completed_v0855.txt`.
- Complément de traduction des notices techniques brèves en cinq langues.
- Ajout des tests de couverture et du registre des révisions natives prioritaires.

## Intégrité fonctionnelle

Aucune modification de l'algorithme d'alignement, de la sélection de lignes, de la segmentation ALTO/PAGE, de la lecture IIIF, du format `.vsynch`, de la sauvegarde ou du format JSON pour Varians. Seule la constante de version change dans `core.py`.

## Validation linguistique

Le nombre de traductions est **complet au sens de la présence de textes localisés**, mais leur validation académique définitive **par des locuteurs natifs et par des spécialistes de l'édition critique** reste à effectuer, en particulier pour les avertissements de validation et la terminologie ecdotique. Voir `docs/I18N_NATIVE_REVIEW_V0855.md`.
