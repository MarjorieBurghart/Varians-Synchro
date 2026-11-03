# Export vers Varians : contrats exacts et limites

## A. JSON de synchronisation (sans TEI obligatoire)

`varians_export.make_varians_alignments(project, base_witness_id)` produit, en mémoire, un objet pour chaque témoin : `meta.format = "tei-manuscript-alignment"`, `format_version = 1`, `witness`, `base_witness`, `role`, et `pages[].lines[]`. Chaque ligne porte sa géométrie, son texte HTR et son ordre ; les lignes des témoins secondaires peuvent avoir des `base_keys`. Les **clés du témoin de base ne sont pas destinées à se référer à elles-mêmes** : ne pas signaler leur absence comme un bug.

Exemple abrégé de **ligne secondaire**, sans garantie de validité TEI :

```json
{
  "line": 12, "order": 44,
  "bbox": {"hpos": 120.0, "vpos": 450.0, "width": 760.0, "height": 48.0},
  "alto_id": "line_abc", "alto": "texte HTR",
  "base_keys": ["page-Mu-4r::10"]
}
```

`base_keys` identifie ici une **ligne physique** de la page `page-Mu-4r`, ordinal 10, et **pas** l'identifiant d'un `<lb>` TEI. `meta.editorial_tei_alignment = "NOT_ESTABLISHED"` l'explicite. Un JSON correctement formé n'établit donc **pas** à lui seul la synchronisation édition↔manuscrits.

`varians_export.export_varians_alignments` prépare atomiquement dans un **dossier vide** :

```text
validated/Mu.json   validated/F.json   ...
working/Mu.json     working/F.json     ...
rapport_export.json
```

- `validated/` : groupes `state=validated` et `kind=correspondence` admissibles ; absences ne deviennent pas des `base_keys`.
- `working/` : ajoute les propositions `uncertain` ; ce sont des hypothèses de travail.
- Lignes **ignorées** : exclues des tableaux exportés, afin d'éviter les faux `<lb/>` obligatoires dans Varians ; leurs numéros physiques d'origine sont préservés et non renumérotés.
- Lien périmé : exclu. `varians_export._safe_same_segmentation_after_format_change` n'admet une continuité ALTO/PAGE via PERO UUID que si ancien et nouveau texte/géométrie coïncident.
- Session A↔F : uniquement si directe avec le pivot choisi ; aucune composition A↔Mu↔F automatique.
- Vérifications : `verify_export_payloads` exige que toutes les `base_keys` présentes chez les secondaires désignent une ligne **active** réellement exportée du pivot ; `inspect_varians_export` explicite notamment les cas `no_direct_session`, `no_saved_links`, `working_only` et `stale_or_ignored`.

CLI : `python exporter_json_varians.py PROJET.vsynch --base Mu --output DOSSIER_VIDE`, puis `python verifier_base_keys_json.py DOSSIER_VIDE/validated/F.json`. Le second script vérifie des comptes locaux ; la vérification **croisée** de toutes les clés est faite par `verify_export_payloads`.

## B. Projet Varians complet (TEI pivot obligatoire)

`varians_project_export.export_varians_project(project,pivot_id,destination,include_uncertain=False)` exige **exactement une** ressource TEI du témoin pivot, des sigles compatibles avec les chemins, des sources présentes et des contraintes de sources images compatibles avec le projet Varians visé (par témoin : pas de mélange local/IIIF ni plusieurs Manifests IIIF). Il prépare notamment `project.xml`, `xml/edition.xml`, `alignments/<sigle>.json`, `rendering/`, `i18n/`, `web_output/` et, si admissibles, les copies HD locales IIIF.

Le fichier TEI est **copié**, jamais réécrit. Les sources ALTO/PAGE et les images locales restent référencées à leur **chemin d'origine** : le paquet peut donc **ne pas être portable**. Les ressources IIIF et les XML de synchronisation font l'objet d'un contrôle avant publication. Le dossier non vide est refusé ; le staging sert à éviter un projet à moitié écrit.

## Compatibilité entre produits

Le contrat historique a été établi avec Varians **0.8.5.2**, et le code indique les conventions Varians 0.8.x. Cette attestation de structure **n'est pas une recette d'import avec les builds actuels de Varians**. Pour chaque sortie : vérifier schéma, comptes pages/lignes, Canvas, correspondance des noms d'images et résolution des `base_keys`, puis ouvrir dans la version exacte de Varians utilisée ; comparer visuellement une sélection Mu/F/L de lignes et polygones. La TEI pivot présente dans un projet généré ne prouve pas que toutes ses balises `<lb/>` correspondent aux clés physiques.

## Critères de non-livraison

Bloquer une sortie pour références du pivot inexistantes, lien périmé utilisé, écrasement d'un dossier non vide, métadonnées de sources corrompues ou perte de géométrie. Avertir — sans mensonge scientifique — quand le seul obstacle est l'absence de liaison TEI↔physique ou de copies HD.

**Tests clés** : `tests/test_varians_export.py`, `test_varians_export_audit.py`, `test_source_integrity.py`, `test_hd_registry_0853.py`, `test_finalization_0851.py`.
