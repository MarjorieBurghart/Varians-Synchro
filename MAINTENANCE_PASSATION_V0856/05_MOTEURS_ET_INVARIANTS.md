# Moteur de correspondance : algorithmes et invariants

## Distinction capitale entre unités

**Ligne physique** : unité géométrique reconnue dans ALTO/PAGE et liée à une page documentaire ; **ligne TEI** : jalon `<lb/>` dans une édition ; **groupe de correspondance** : association entre des ensembles non vides de lignes de deux témoins ; **absence attestée** : observation éditoriale confirmée sur un côté ; **hors périmètre** : ligne physique conservée mais volontairement exclue. Ces catégories ne sont **jamais synonymes**.

## Construction et ordre du flux

`imaging.mapped_alto_page` récupère la segmentation associée à chaque page, `physical_alignment.physical_lines` construit les fiches et empreintes, `reading_stream.reading_stream` ordonne la lecture et exclut les lignes désignées hors périmètre. `page_order.ordered_pages` fait respecter l'ordre explicite quand il existe, sinon les informations folio/ordre naturel ; `reading_stream.set_page_order`, `set_region_order`, `set_line_order` enregistrent les corrections humaines.

Le moteur travaille au-delà des colonnes et folios. L'ordre de lecture choisi fait partie des preuves de liaison TEI et des repères de correspondance : un réordonnancement doit invalider les prévisualisations devenues périmées.

## Groupes physiques `physical_alignment.py`

`create_pair_session(project, A, B)` refuse deux fois le même témoin, exige des lignes associées et réutilise la session déjà présente pour la même paire **sans tenir compte de l'orientation**. `add_pair_link` impose `KINDS`, `STATES`, l'existence des UID actifs et l'absence de double utilisation d'une ligne dans les groupes de cette session. Il enregistre les empreintes et l'origine ; une paire F↔L ne crée jamais transitivement un lien via Mu.

- `extend_pair_link` étend **un** groupe existant sans fusion implicite, conserve l'identifiant et les preuves de correction ; n'augmente pas automatiquement `uncertain` vers `validated`.
- `detach_pair_lines` permet la correction locale ; vérifier les cas d'absence et groupes vidés.
- `replace_revisable_pair_proposals` évalue d'abord les conflits et travaille sur une copie profonde de la session ; les liens manuels/validés protégés ne sont pas supprimés.
- `set_pair_link_states` exige l'existence de tous les IDs demandés et inscrit une date de révision en cas de validation.
- `verify_pair_sessions` et `pair_progress` signalent lignes disparues ou dont le fingerprint diverge ; ils **ne réparent pas** les liens.

## Groupes périmés (nouvelle segmentation d'une page)

Une ligne est identifiée par sa page et son rang (`line_uid`). Si une page reçoit un autre XML, un groupe peut désigner d'autres lignes. Un groupe est **périmé** quand une de ses lignes a disparu ou que son empreinte (`fingerprints`) ne correspond plus à la ligne actuelle (`physical_alignment.link_is_stale`, `stale_link_ids`). Il n'est jamais supprimé, mais :

- il n'est jamais une ancre (`reading_stream.anchor_intervals` : avertissement `stale_anchor` ; `interpolation.suggest_between_anchors`) ni un obstacle sûr (`textual_progress` : `stale_protected_link`) ;
- `extend_pair_link` le refuse (recalculer ses empreintes effacerait la trace du changement) ;
- l'export l'écarte (contrôle d'empreintes de `varians_export`) ;
- l'interface le marque « [périmé] », le filtre « Périmés » le liste (`rapid_review.FILTER_STALE`), et « Revalider… » (`revalidate_pair_links`, tout ou rien, refusé si une ligne a disparu) relève à nouveau ses empreintes après vérification humaine, avec trace dans `evidence.manual_corrections`.

Avant de donner un autre XML à une page, l'interface dit ce que cela touche (`page_links_impact` : groupes par statut, ordre de lecture corrigé) ; `reading_stream.rebind_page` associe la page et retire son ordre de lecture corrigé si son XML change. Tests : `tests/test_stale_links.py`, `tests/test_stale_links_qt.py`.

## Propositions et niveau de preuve

| Mécanisme | Module | Rôle | Limite à respecter |
|---|---|---|---|
| HTR/texte | `automatic.py`, `physical_alignment.suggest_htr_pair_alignment` | Similarités séquentielles et groupes candidats | HTR peut être incomplet ; un groupe multi↔multi trop grossier doit rester incertain |
| Progression cumulée V0.7.4 | `textual_progress.py` + `reading_stream.anchor_intervals` | Partitions entre repères, estimation par quantité de texte | Préserver les ancres et isoler les intervalles croisés |
| Interpolation | `interpolation.py` | Complément géométrique et/ou textuel entre repères | Suggestion, pas remplacement silencieux d'une validation |
| Résiduelles | `residual_alignment.py` | Propose d'étendre des groupes existants à des lignes orphelines | Traces `evidence.residual_extensions`, prudence sur les colonnes |
| Relecture rapide | `rapid_review.py`, `review.py` | Filtres, progression, validations en série | Vérifier fraicheur et sélection avant validation |
| Absences confirmées | `exceptions.py` | Prévisualisation puis inscription d'une absence motivée | Aucun inventaire de « non liées » ne vaut une absence |
| Périmètre | `line_scope.py` | Exclusion/réintégration de lignes physiques | Conflits à résoudre dans **toutes** les sessions concernées |

Dans `textual_progress._weights` : HTR utilisable si longueur plausible ; sinon largeur géométrique, calibrée par région, puis normalisation uniforme. Le calcul est par **intervalles entre repères**, non un étirement aveugle de toute une page. Cette hiérarchie est documentairement motivée, mais sa précision dépend de la qualité du HTR et du réglage des repères.

## Invariants qui doivent rester couverts par des tests

1. Une ligne active ne figure pas deux fois dans la même paire, même dans deux groupes différents.
2. Les liens sauvegardés incluent les empreintes des lignes réellement visées ; ne pas remplacer un lien périmé par le lien « le plus proche ».
3. Un recalcul n'efface jamais une validation humaine ou un groupe protégé sous prétexte d'optimiser la couverture.
4. Un groupe manuel peut être N↔M ; une coïncidence HTR ne suffit pas à résoudre une segmentation différente.
5. Une ligne ignorée n'est ni supprimée de la source, ni transformée en absence.
6. Des témoins liés chacun au pivot ne sont pas présumés synchronisés l'un avec l'autre.
7. L'import ALTO↔PAGE conserve le champ historique `alto_binding` et ses identifiants. La reconnaissance d'un même UUID PERO n'autorise la récupération qu'avec contrôle de texte et géométrie, pas sur l'ordre seul.
8. Les procédures d'audit sont en lecture seule et ne « nettoient » pas un projet.

**Références de tests** : `tests/test_physical_alignment.py`, `test_textual_progress.py`, `test_reading_stream.py`, `test_full_column_interpolation.py`, `test_residual_alignment.py`, `test_confirmed_exceptions.py`, `test_ignored_lines.py`, `test_recalculation_existing_proposals.py`, `test_manual_group_editing.py`.
