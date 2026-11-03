# Risques connus, dette technique et périmètre de validation

| Priorité | Point | Conséquence | Mesure recommandée |
|---|---|---|---|
| Haute | `.vsynch` dépend d'UID basés sur page + ordinal | Nouvelle segmentation peut laisser des liens trompeurs ou périmés | `verify_pair_sessions`, comparaison des empreintes, migration manuelle contrôlée |
| Haute | `base_keys` du JSON d'alignement sont physiques | Le navigateur de Varians peut ouvrir un JSON pourtant décalé de la TEI | Vérifier `<lb/>`, documenter « NOT_ESTABLISHED », recette d'import réelle |
| Haute | Compatibilité export projet vérifiée avec Varians 0.9.4.0 seulement (`tests/test_varians_094_compat.py`) | Une nouvelle version de Varians peut changer ses attentes | Changer `VARIANS_REF` dans la CI et faire passer ces tests |
| Haute | Origine scientifique des absences et validations | Faux positifs philologiques irréversibles si acceptés en bloc | Prévisualisation, provenance et contrôle humain |
| Haute | Copies HD partielles ou modifiées | Canvas manquants, ressources cassées | Contrôle SHA-256 et couverture complète **par témoin** |
| Moyenne | `guided_ui.py` monolithique | Refactoring délicat et tests GUI coûteux | Découpage progressif sous tests régression ouverture/enregistrement |
| Moyenne | Couverture Qt limitée lorsque PySide6 absent | Scénarios interactifs non vérifiés par CI headless | Recette GUI sur Windows + tests Qt sur Linux/macOS si disponibles |
| Moyenne | Chemins absolus vers sources externes | Projet exporté non entièrement portable | Rapport explicite, relocalisation manuelle contrôlée |
| Moyenne | Serveurs IIIF intermittents, quota, variantes v2/v3 | Vignettes et téléchargement non disponibles | Diagnostic réseau et distinction de panne vs données absentes |
| Moyenne | Traduction « complète » seulement par catalogues | Terme technique imprécis / libellé tronqué | Relecture native selon `docs/I18N_NATIVE_REVIEW_V0855.md` |
| Moyenne | Schéma `.vsynch` peu contraignant côté `validate_project` | Une structure mal formée peut échapper à validation initiale puis échouer plus tard | `validation.audit_project`, schéma JSON formel futur et tests de corruption |
| Basse | Script `recette_v085.py` historique | Identifiant rapport version fixe, peut être confondu avec version de livraison | Documenter et versionner le protocole d'audit si on le modifie |
| Basse | Documentation rétrospective dispersée | Un ancien guide peut contredire l'état courant | Ce dossier fait autorité pour la reprise, mais **code et tests** arbitrent les faits |

## Tâches ouvertes **sans prétendre les avoir exécutées**

1. Passer intégralement la recette GUI et Spyder sur Windows 11 avec une installation réelle PySide6, comparer les captures en sept langues.
2. Importer un projet exporté v0.8.5.6 dans le build Varians effectivement déployé et vérifier les Canvas, polygones, `base_keys` et l'alignement éditorial sur pages choisies.
3. Faire valider par locuteurs natifs les choix terminologiques des cinq langues ajoutées en v0.8.5.5, y compris confirmations de validation et absence.
4. Envisager un schéma formel `.vsynch` (`jsonschema` facultatif) et des tests de corruption hostiles **sans casser** les projets anciens.
5. Ajouter une CI matrice Windows/Linux/macOS (Qt présent et absent), ainsi que des fixtures IIIF locales v2/v3, sans accès réseau dans les tests déterministes.
6. Qualifier formellement la portabilité de l'export projet, aujourd'hui liée aux chemins d'origine ; ne pas prétendre livrer des sources autonomes tant qu'elles sont externes.

## Ce qui n'est PAS une anomalie

- JSON du pivot sans `base_keys` ; les `base_keys` résident dans les secondaires.
- Absence de TEI dans un projet commencé avec de simples images ou ALTO ; c'est une capacité souhaitée.
- Existence des dossiers `working` et `validated` : deux niveaux de preuve distincts.
- Présence de champs historiques tels que `alto_binding` et `alignment_sessions` malgré la refonte.
- Des avertissements de chemins vers des sources déplacées après copie d'un projet.
