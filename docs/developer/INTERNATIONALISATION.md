# Internationalisation

L'interface de Varians-Synchro existe en sept langues : français, anglais, allemand, tchèque, italien, russe et japonais. Toute nouvelle phrase visible doit exister dans les sept. Les données ne sont **jamais** traduites : transcriptions HTR et TEI, sigles, libellés de folios, identifiants, chemins, URL.

## Catalogues

Un fichier XML par langue, `i18n/<langue>.xml`, de même schéma que ceux de Varians :

```xml
<translations lang="fr" label="Français">
  <string key="navigation.alignment">3 · Aligner les témoins</string>
</translations>
```

`varians_synchro/i18n.py` les charge au démarrage et refuse un catalogue où il manque une clé, où une clé est répétée ou vide, ou dont les paramètres `{nom}` diffèrent de ceux du français. Les sept catalogues ont donc exactement les mêmes clés (693 à ce jour ; `docs/i18n_coverage.json`, contrôlé par `tools/check_maintenance.py`).

Une valeur peut s'étendre sur plusieurs lignes : pour ajouter une clé, l'insérer juste avant `</translations>` dans les sept fichiers, jamais au milieu d'une autre entrée.

## Dans le code

- `tr('clé', nom=valeur)` donne le texte dans la langue courante (`set_language`, `get_language`). Une valeur française du catalogue sert aussi d'alias de sa clé : `tr('Exporter JSON pour Varians…')` est traduit comme `tr('export.varians.action')`. Un texte inconnu est rendu tel quel, sans rapprochement approximatif : un identifiant ou une donnée n'est jamais traduit par erreur.
- Les boîtes de message, étiquettes et boutons de `ui_widgets.py` passent leurs textes par `tr` ; les boutons standard de Qt (« OK », « Close »…) ne sont pas traduits par Qt dans toutes les langues : utiliser des boutons à libellé traduit.
- Les moteurs (sans Qt) écrivent leurs erreurs et avertissements en français : c'est le texte de `str(exc)`, des journaux et des tests. Un message fixe est la valeur française d'une clé du catalogue. Un message avec des valeurs (un sigle, un fichier) n'est jamais composé à la main : `raise localized(ValueError, 'error.scope.unknown_witness', witness=sigle)`, ou `Localized('clé', …)` pour un avertissement (module `errors.py`) ; la chaîne reste française et garde sa clé et ses valeurs. Les fenêtres affichent toute erreur par `localized_text(exc)`, jamais par `str(exc)`. `tests/test_engine_messages_i18n.py` le vérifie pour tous les moteurs ; seules quelques erreurs de programmation, qu'aucun utilisateur ne peut provoquer, restent hors catalogue.
- La langue choisie est mémorisée par `QSettings('Varians', 'Varians-Synchro')` ; changer de langue reconstruit la fenêtre sans toucher au projet en mémoire.

## Aide

Le guide utilisateur, `help/<langue>.html`, existe dans les mêmes sept langues. Chaque libellé d'écran qu'il cite est balisé (`data-tr` pour Varians-Synchro, `data-varians` pour Varians) ; `python tools/help_labels.py` le remplit d'après les catalogues, et `tests/test_help_guides.py` vérifie qu'il est celui de l'écran.

## Tests

`test_i18n.py`, `test_i18n_xml_catalogs.py` et `test_i18n_full_0855.py` (catalogues, clés, paramètres), `test_i18n_fragment_spacing.py` (espaces des fragments mis bout à bout), `test_terminology.py` (termes alignés sur Varians), `test_alignment_errors_i18n.py`.

## Relecture

Les traductions sont complètes, mais n'ont pas toutes été relues par des locuteurs natifs spécialistes de la critique textuelle : vocabulaire éditorial, pluriels et rendu dans Qt restent à vérifier (`docs/I18N_NATIVE_REVIEW_V0855.md`).
