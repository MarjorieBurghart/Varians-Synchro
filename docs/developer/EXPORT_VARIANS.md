# Export vers Varians

Varians-Synchro donne à Varians ce qu'il lui faut pour synchroniser une édition TEI avec les images des manuscrits : un fichier de synchronisation JSON par témoin, ou un projet Varians complet. Ce document en résume le fonctionnement pour qui maintient le code ; le détail des contrats est au chapitre [08 du dossier de passation](../../MAINTENANCE_PASSATION_V0856/08_EXPORT_VERS_VARIANS.md), le mode d'emploi et la description champ par champ du JSON dans l'aide (`help/<langue>.html`, sections « Étape 4 » et « Format des fichiers de synchronisation »).

Compatibilité vérifiée : **Varians 0.9.4.0** (`tests/test_varians_094_compat.py` et `tests/test_varians_blank_edition.py` ouvrent l'export avec le vrai code de Varians ; la CI le récupère à la version `VARIANS_REF`).

## Les deux exports

Tous deux sont dans **4 · Finaliser** et écrivent dans un dossier vide, préparé à part puis publié d'un bloc (pas de résultat à moitié écrit).

| Commande | Module | Usage |
|---|---|---|
| **Créer un projet Varians pré-renseigné…** | `varians_project_export.export_varians_project` | Nouveau projet Varians (parcours A de l'aide) : `project.xml`, `xml/edition.xml` (la TEI du pivot copiée telle quelle, sinon la TEI vide de Varians), `alignments/<sigle>.json`, dossiers habituels, copies HD IIIF éventuelles. |
| **Exporter JSON pour Varians…** | `varians_export.export_varians_alignments` | Ajouter ou mettre à jour un témoin d'un projet Varians existant (parcours B) : `validated/<sigle>.json`, `working/<sigle>.json`, `rapport_export.json`. |

En ligne de commande, sans PySide6 :

```bash
python exporter_json_varians.py projet.vsynch --base Mu --output dossier_vide
python verifier_base_keys_json.py dossier_vide/validated/F.json
```

## Ce que contient un fichier de synchronisation

Format `tei-manuscript-alignment`, version 1, produit par `varians_export.make_varians_alignments`. Le test `tests/test_help_guides.py` vérifie que l'aide documente exactement les champs écrits.

- Le fichier du **pivot** décrit ses lignes retenues, dans l'ordre de lecture (`reading_stream`). Varians fait correspondre la *n*-ième ligne au *n*-ième `<lb edRef="#PIVOT"/>` de l'édition et vérifie que les nombres sont égaux ; s'il n'y a pas encore de `<lb/>`, Varians les prépare d'après ce fichier (Paramètres du projet).
- Chaque **autre témoin** relie ses lignes à celles du pivot par `base_keys`, de la forme `id_de_page::rang` (`pages[].id` et `pages[].lines[].line` d'une ligne du pivot). Ces clés sont physiques : elles restent valables tant que la page du pivot garde son identifiant et son fichier ALTO/PAGE. D'où la règle du parcours B : aligner le nouveau témoin dans le même `.vsynch`, sans toucher au pivot.
- Les lignes **ignorées** ne sont pas écrites ; les rangs `line` ne sont pas renumérotés.
- `meta.editorial_tei_alignment = "NOT_ESTABLISHED"` : le fichier ne contient aucun lien vers la TEI ; c'est Varians qui l'établit, par l'ordre des `<lb/>`.

## Règles de l'export

- `validated/` : seulement les groupes validés de type correspondance ; `working/` y ajoute les propositions non validées. Varians ne connaît pas ces états (`vsynch_state` est informatif) : importer `validated/`, sauf essai en connaissance de cause.
- Seules les synchronisations **directes** avec le pivot sont exportées : aucune composition A↔Mu↔F.
- Une absence confirmée ne produit pas de `base_keys`.
- Un lien **périmé** est exclu, sauf continuité ALTO↔PAGE démontrée (même UUID PERO, texte et géométrie inchangés) ; jamais de rapprochement par simple ordre de ligne.
- `verify_export_payloads` refuse l'export si une `base_keys` ne désigne pas une ligne réellement exportée du pivot ; `inspect_varians_export` dit, avant l'export, pourquoi un témoin n'aurait aucune correspondance (`no_direct_session`, `no_saved_links`, `working_only`, `stale_or_ignored`).
- Les images et les fichiers ALTO/PAGE restent à leur place : le projet ou le JSON pointe vers eux, avec les chemins du projet source.
