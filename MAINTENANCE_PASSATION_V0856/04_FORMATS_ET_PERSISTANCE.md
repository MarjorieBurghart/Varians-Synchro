# Contrats des données et persistance

## Deux numéros de version indépendants

- Version de l'application : `core.VERSION == '0.8.6.0'`.
- Version persistée `.vsynch` : `format: "varians-synchro-project"`, `version: 1` (`core.SCHEMA`, `new_project`, `validate_project`). Ne pas incrémenter le format pour une version **de documentation**.

## Schéma JSON (exemple minimal illustratif)

```json
{
  "format": "varians-synchro-project", "version": 1,
  "name": "Exemple", "created": "2026-10-19T00:00:00+00:00",
  "pivot_witness_id": "Mu", "workflow_preference": "alto_only",
  "witnesses": [{"id":"Mu", "label":"Munich", "image_sources":[],
     "alto_sources":[], "pages":[], "ignored_line_ids":[]}],
  "text_resources":[], "alignment_sessions":[], "pair_sessions":[], "notes":""
}
```

`workflow_preference` (`alto_only`, `pivot`, `tei`) configure un parcours d'interface, pas le nombre de ressources autorisées. `pivot_witness_id` est `null` ou l'ID d'un témoin connu. `alignment_sessions` conserve les sessions historiques TEI ; `pair_sessions` contient les paires physiques nouvelles et reste un modèle distinct.

## Entités et référence de vérité

| Entité | Clé et origine | Contrainte |
|---|---|---|
| Témoin | `witnesses[].id` (sigle) | Unique ; ne pas renommer après création sans migration de toutes références |
| Source image | `image_sources[].id` UUID | `kind` local/iiif, `reference`, inspection éventuelle |
| Source ALTO/PAGE | `alto_sources[].id` UUID | champ `kind` absent = ancien ALTO ; `pages[].lines[]` instantané, SHA-256 du fichier |
| Page documentaire | `witnesses[].pages[].id` | Image locale/Canvas ; `alto_binding` pointe vers `source_id` + `page_index` |
| Ligne physique | `urn:vsynch:line:<uuid5>` | `physical_alignment.line_uid(witness_id,page_id,ordinal)` ; dépend de l'identité de page et de son ordinal physique |
| Session de paire | `pair_sessions[].id` UUID | Couple de témoins non orienté au sens documentaire, orienté seulement dans sa représentation |
| Groupe | `pair_sessions[].links[].id` UUID | N↔M ; `reference_ids`, `target_ids`, `state`, `kind`, `fingerprints` |
| Ressource TEI | `text_resources[].id` UUID | TEI externe référencée, `source_sha256`, `tei_binding` facultatif |
| Registre HD | `witnesses[].hd_downloads[]` | Références de lots `images.json` validés, liées au Canvas et à l'URL IIIF |

Un UID physique reste stable **à condition** que témoin, identifiant de page et position ordinale dans la source soient inchangés. Un changement de segmentation qui décale un ordinal est donc une modification *sémantique* à auditer, même si le générateur d'UID redonne une chaîne syntaxiquement valide.

### Exemple de groupe physique

```json
{
  "id": "uuid-lien", "reference_ids": ["urn:vsynch:line:uuid-a"],
  "target_ids": ["urn:vsynch:line:uuid-b1", "urn:vsynch:line:uuid-b2"],
  "kind": "correspondence", "state": "validated", "origin": "manual",
  "fingerprints": {"urn:vsynch:line:uuid-a": "empreinte-hex", "urn:vsynch:line:uuid-b1":"empreinte-hex", "urn:vsynch:line:uuid-b2":"empreinte-hex"}
}
```

Les champs ci-dessus n'étant que schématiques, les valeurs `uuid-a` ne sont **pas** des UID utilisables. L'empreinte de ligne physique actuelle couvre `[alto_id, bbox, text]`, pas les métadonnées de région ou polygone ajoutées ultérieurement (`physical_alignment.physical_lines`).

## Absences, périmètre et états

- `kind=correspondence` : au moins une ligne sur **chaque** côté.
- `kind=absence` : **exactement** un côté est vide ; une absence est une décision explicitement enregistrée, et non une case « non associée ».
- `state` : `proposed`, `uncertain`, `validated` ; une révision humaine modifie le statut, pas la réalité historique de la source.
- `ignored_line_ids` : hors périmètre d'étude pour ce **témoin** ; n'est pas une omission et ne doit pas engendrer une fausse ligne TEI.
- `review_settings` permet notamment `mode` et `threshold` au niveau session.

## Lecture, migration, sauvegarde

`load_project` valide format/version puis complète **en mémoire** les valeurs historiques manquantes (par exemple `pair_sessions`, `pivot_witness_id`, `workflow_preference`) : ouvrir n'est pas sauvegarder. `core.save_project` valide, sérialise UTF-8, écrit un fichier temporaire dans le dossier cible, synchronise le fichier, écrit si nécessaire une copie `.vsynch.bak` des **octets antérieurs**, puis publie avec `os.replace`. **Aucune copie `.bak` n'est produite au premier enregistrement.** Une erreur I/O peut laisser une copie `.bak` nouvellement préparée, mais ne doit pas altérer l'original tant que le remplacement final n'a pas réussi.

**Chemins relatifs.** Un chemin de fichier relatif (`image_sources[].reference` d'une source locale, `alto_sources[].path`, `pages[].image_path`, `hd_downloads[].directory`, `text_resources[].path`) est lu par rapport au dossier du fichier `.vsynch`, avec « / » ou « \ » comme séparateur. Les chemins absolus (POSIX ou Windows, même venant d'un autre système) et les URL ne changent pas. En mémoire, les chemins sont absolus ; à l'enregistrement (`core._with_relative_paths`), un fichier situé dans le dossier du `.vsynch` ou en dessous est écrit en chemin relatif à séparateurs « / », un fichier ailleurs (autre dossier, autre disque) garde son chemin absolu : un projet rangé avec ses fichiers voyage avec eux (`tests/test_relative_save.py`). L'exemple livré (`demo_local_ALTO/`) n'a que des chemins relatifs : il s'ouvre tel quel, où que soit le dépôt (`tests/test_relative_paths.py`).

Le contrôle des modifications non enregistrées utilise `project_state.ProjectChangeTracker` et un SHA-256 de la représentation JSON complète, pas seulement des événements UI. Ne remettre le repère « enregistré » à zéro qu'après succès disque (`mark_saved`).

## Compatibilité et migrations futures

Ne pas réutiliser `version: 1` pour un changement cassant. Pour ajouter un champ optionnel : gérer son absence à l'ouverture, fixer une valeur explicite à la création, mettre à jour validation/tests/doc, conserver les anciens témoins et sessions. Pour modifier UID/fingerprint/`alto_binding`, écrire une migration **explicite, réversible et testée** ; ne pas reconstruire silencieusement les liens. Un ancien projet peut contenir des `text_resources` TXT/MD historiques qui ne sont plus importables depuis l'interface actuelle mais restent **préservés** à la lecture.
