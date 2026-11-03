# Varians-Synchro v0.8.5.5 — Registre de relecture linguistique

## Portée et honnêteté éditoriale

- **Couverture technique :** 653 entrées dans chacun des sept fichiers `i18n/*.xml` ; aucune des 244 clés qui utilisaient explicitement un repli anglais n'est restée sans texte localisé.
- **Contrôles automatisés :** égalité des clés, conservation des noms des paramètres et capacité de formatage, intégrité XML et non-traduction des identifiants métier.
- **Ce qui n'a pas été établi :** validation par des traducteurs natifs, contrôle systématique de la taille des libellés dans les interfaces Qt réelles et acceptabilité de chaque expression dans la tradition académique nationale.
- Les 409 traductions préexistantes par langue ont été conservées en très grande majorité : la couverture à 100 % n'en constitue pas un audit linguistique exhaustif.

## Priorité 1 — conséquences éditoriales et actions potentiellement irréversibles

À faire vérifier *dans les cinq langues*, avec affichage du contexte de dialogue :

| Clé | Question de traduction | Risque |
|---|---|---|
| `exception.confirm` | absence textuelle confirmée dans **l'autre** témoin, protection des liens validés | inversion de la portée de la confirmation |
| `exception.revoke.confirm` | retrait de l'affirmation d'absence, sans supprimer de lignes | confusion « supprimer » / « délier » |
| `alignment.export.policy_text` | propositions exploratoires non validées vs liens validés | export de données non vérifiées |
| `export.varians.warning` | références physiques vs éléments `<lb/>` de l'édition | croire à une synchronisation TEI déjà assurée |
| `export.varians.audit_warning` | absence normale de `base_keys` pour le témoin pivot | fausse alerte ou contresens |
| `alignment.residual.confirm.text` | extension des seuls groupes automatiques incertains | risque de croire à la modification des liens protégés |
| `ui.pages.hd.unregistered` | images téléchargées mais lot **non enregistré** dans le projet | fausse impression de sauvegarde |
| `tei.visual.no_images_confirm` | confirmation sans contrôle des deux images d'extrémité | validation insuffisante |

## Priorité 2 — terminologie savante à arbitrer par la communauté

- **DE :** *Textzeuge*, *Referenztextzeuge*, *Lesereihenfolge*, *Fehlstelle*, *Anker*, *Zuordnung* et *Synchronisierung*. La différence entre absence matérielle et omission textuelle doit être claire.
- **CS :** *svědek*, *referenční svědek*, *kotva*, *zarovnání*, *absence / vynechání* ; harmoniser avec les usages des éditions critiques tchèques.
- **IT :** *testimone*, *testimone di riferimento*, *ancora*, *allineamento*, *assenza / omissione* ; vérifier que le mot *ancora* est adéquat comme métaphore d'interface.
- **RU :** *свидетель текста / свидетель*, *опорный текст*, *опорная точка*, *отсутствие / пропуск* ; unifier la terminologie de critique textuelle (et non juridique).
- **JA :** *伝本*, *参照伝本*, *対応付け*, *アンカー*, *欠落 / 脱落*, *校訂版 / 翻刻* ; vérifier tout spécialement la distinction entre le témoin manuscrit, l'édition critique et le texte pivot.

Clés pour comparer la terminologie en contexte : `project.mode.pivot`, `project.mode.tei`, `alignment.mode.rigorous`, `progress.warning.one_sided_gap`, `pages.order.tab_help`, `tei.binding.help`, `ui.audit.issue.secondary_only_uncertain`, `ui.audit.issue.tei_binding_stale`.

## Priorité 3 — taille et rendu graphique

- Allemand et russe : vérifier les boutons de confirmation, les titres et les infobulles longues ; certaines chaînes se dilatent.
- Tchèque : vérifier les terminaisons flexionnelles autour des compteurs `{count}`, `{groups}`, `{lines}`. Pour un futur véritable pluriel (1 / 2–4 / 5+), le schéma d'internationalisation devra évoluer ; cela **n'est pas corrigé par la simple traduction**.
- Russe : même risque de flexion pour 1 / 2–4 / 5+ ; préférer des formulations neutres ou introduire des règles pluriels dans une prochaine évolution.
- Japonais : vérifier la distinction entre boutons et messages, la ponctuation `？` et l'affichage des termes latins/TEI ; contrôler les retours à la ligne et la largeur du panneau.
- Vérifier les codes `Ctrl`, `Shift`, `Ctrl+A` par rapport aux raccourcis Qt disponibles sur chaque plateforme.

## Protocole suggéré pour la validation native

1. Ouvrir les quatre étapes de l'assistant et les fenêtres de synchronisation dans la langue choisie.
2. Déclencher l'export non validé, la confirmation d'absence, le retrait d'absence et un échec de téléchargement HD.
3. Vérifier la sémantique des protections, la non-traduction des identifiants et les retours à la ligne.
4. Corriger uniquement les valeurs des clés XML ; conserver toutes les clés et tous les paramètres exactement.
5. Exécuter `python -m pytest -q` après toute correction et actualiser les empreintes SHA-256 du paquet.

La liste complète des 244 clés nouvellement traduites figure dans `docs/i18n_completed_v0855.txt`.
