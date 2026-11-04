# Format des projets `.vsynch`

Un projet Varians-Synchro est un fichier JSON en UTF-8 : `format: "varians-synchro-project"`, `version: 1`. Ce numéro de format est indépendant de la version du logiciel (`core.VERSION`) et n'a pas changé depuis V0.5 : chaque ajout ci-dessous est facultatif, et un projet plus ancien reste lisible. Les contrats à préserver (identité des lignes, empreintes, sauvegarde, migrations) sont au chapitre [04 du dossier de passation](../../MAINTENANCE_PASSATION_V0856/04_FORMATS_ET_PERSISTANCE.md) ; ce document décrit le contenu du fichier.

Ce format n'est pas celui que lit Varians : l'export le convertit en fichiers de synchronisation `tei-manuscript-alignment` (voir [`EXPORT_VARIANS.md`](EXPORT_VARIANS.md)).

## Racine

| Champ | Contenu |
|---|---|
| `name`, `created`, `notes` | Nom du projet, date de création (ISO 8601), notes libres. |
| `pivot_witness_id` | Le sigle du témoin pivot, ou `null`. Le premier témoin ajouté devient pivot par défaut ; changer de pivot ne modifie pas les associations enregistrées. |
| `workflow_preference` | `alto_only`, `pivot` ou `tei` : une préférence d'interface, pas une limite du projet. |
| `witnesses` | Les témoins (ci-dessous). |
| `text_resources` | Les éditions TEI des témoins (ci-dessous). |
| `pair_sessions` | Les synchronisations entre deux témoins (ci-dessous). |
| `alignment_sessions` | Anciennes sessions TEI–ALTO, conservées telles quelles. |

`load_project` complète en mémoire les champs absents d'un projet ancien, sans réécrire le fichier ; `save_project` écrit d'abord un fichier temporaire, garde l'état précédent dans `.vsynch.bak`, puis le remplace.

**Chemins.** Un chemin relatif (image locale, fichier ALTO/PAGE, TEI, dossier HD) est lu par rapport au dossier du `.vsynch`, avec « / » ou « \ » comme séparateur ; en mémoire, tous les chemins sont absolus. À l'enregistrement, un fichier situé dans le dossier du `.vsynch` ou en dessous est écrit en chemin relatif à séparateurs « / » (`core._with_relative_paths`) ; un fichier ailleurs garde son chemin absolu. Un projet rangé avec ses fichiers peut donc être déplacé ou copié.

## Témoins

Chaque entrée de `witnesses[]` a pour `id` le sigle du témoin (unique) et un `label`.

- `image_sources[]` : Manifests IIIF ou dossiers d'images locales (`kind` : `iiif` ou `local`, `reference`). Un Manifest qui n'a pas répondu est gardé avec `status: "unavailable"` et `error` ; donner de nouveau son adresse (bouton « Réessayer » de la fiche du témoin) l'interroge une nouvelle fois (`resource_workflow.apply_witness_draft`).
- `alto_sources[]` : fichiers ALTO ou PAGE importés, avec leur empreinte SHA-256 et un instantané de leurs pages et lignes (`pages[].lines[]` : `alto_id`, `text`, `bbox`, et `polygon` si le fichier donne un contour). `kind: "page"` désigne un fichier PAGE ; sans `kind`, c'est un ALTO. Les coordonnées sont celles du fichier, non réécrites.
- `pages[]` : les pages du témoin. Chacune a un `id` stable, son image (`image_kind`, Canvas IIIF ou `image_path`) et, si elle est associée à un fichier, `alto_binding` (`source_id`, `page_index`) — ce nom vaut aussi pour PAGE et ne doit pas être renommé. L'ordre de lecture corrigé est dans `reading_order` (rang de la page), `reading_region_order` et `reading_line_order` (ordre des régions ou des lignes de la page).
- `ignored_line_ids[]` : les lignes hors du périmètre d'étude (marges, titres courants…). Ce n'est ni une omission ni une absence attestée ; une ligne ignorée ne peut pas être associée, et les lignes déjà liées sont dissociées, après confirmation, avant d'être ignorées.
- `hd_downloads[]` : les lots de copies HD d'images IIIF (`directory`, `pages[]` : `canvas_id`, `file`, `iiif_image_url`, `size_bytes`, `sha256`). Ils n'ajoutent ni page ni association.

**Identité d'une ligne.** Une ligne physique est désignée par `urn:vsynch:line:<uuid5>`, calculé par `physical_alignment.line_uid(témoin, page, rang)` : elle reste la même tant que la page garde son identifiant et que la ligne garde son rang dans le fichier ALTO/PAGE.

## Éditions TEI

Une entrée de `text_resources[]` de `kind: "tei"` référence une TEI externe, jamais réécrite : `path`, `witness_id`, `source_sha256`, `lines` (les `<lb/>` lus), `status` (`tei_unaligned` ou `tei_aligned`). `tei_binding` (`witness_id`, `pairs[]` : `physical_line_id`, `tei_key`) relie ses `<lb/>` aux lignes physiques ; `tei_binding.tei_binding_status` le déclare périmé si la TEI, le périmètre ou l'ordre ont changé. Des ressources TXT/MD d'anciens projets sont conservées à la lecture, mais ne s'importent plus.

## Synchronisations

Chaque entrée de `pair_sessions[]` (`kind: "physical-pair"`) relie deux témoins, `reference_witness_id` et `target_witness_id`, par des groupes `links[]` :

```json
{
  "id": "uuid-du-lien",
  "reference_ids": ["urn:vsynch:line:uuid-A-1"],
  "target_ids": ["urn:vsynch:line:uuid-B-1", "urn:vsynch:line:uuid-B-2"],
  "fingerprints": {"urn:vsynch:line:uuid-A-1": "sha256", "urn:vsynch:line:uuid-B-1": "sha256"},
  "kind": "correspondence",
  "state": "validated",
  "origin": "manual"
}
```

- `kind: "correspondence"` : au moins une ligne de chaque côté (groupe n↔m). `kind: "absence"` : une absence confirmée, **exactement** un côté vide ; elle ne se confond pas avec une ligne non synchronisée.
- `state` : `proposed`, `uncertain` ou `validated`. `origin` dit d'où vient le groupe (`manual`, `manual-correction`, `automatic-htr-htr`, `interpolated-residual`…) ; `confidence`, entre 0 et 1, accompagne une proposition automatique.
- `fingerprints` : l'empreinte de chaque ligne au moment du lien (`alto_id`, `bbox`, texte). Un lien dont une ligne a disparu ou changé est **périmé** (`physical_alignment.link_is_stale`) : il n'est jamais effacé, mais il est exclu des calculs et de l'export jusqu'à ce que l'utilisateur le revalide ou le dissocie.
- `evidence` garde l'historique des corrections (`manual_corrections`, `residual_extensions`…) ; `review_settings` règle la révision rapide de la session (`mode`, `threshold`).
