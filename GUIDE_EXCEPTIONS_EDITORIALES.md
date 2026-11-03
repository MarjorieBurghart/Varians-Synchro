# Varians-Synchro V0.7.3 — Exceptions éditoriales et absences confirmées

## Ce que signifie « absence confirmée »

En synchronisant **Mu ↔ F**, sélectionner deux lignes dans **Mu** et confirmer leur absence signifie que le passage de ces lignes de Mu **n’a pas d’équivalent textuel dans F**. Les lignes restent dans le texte édité, et ne sont **pas** ignorées. Cette déclaration concerne uniquement la paire Mu–F : Mu peut rester associé à A dans une autre session.

Une différence de segmentation (deux lignes courtes ↔ une ligne longue) est une correspondance 2↔1, **pas** une absence.

### Trois états distincts

| Statut | Sens | Portée |
|---|---|---|
| Sans correspondance / absence confirmée | Passage attesté dans un témoin mais absent de l’autre | Paire de témoins |
| Ignorée / hors périmètre | Ligne située en dehors du texte étudié | Témoin global |
| Non synchronisée | Équivalent pas encore établi | Paire de témoins |

## Traitement rapide d'une absence

1. Ouvrir la synchronisation visuelle d'une paire.
2. Sélectionner **uniquement les lignes du témoin qui possède le passage**, dans l'image ou la vue textuelle. Elles peuvent traverser une limite de folio.
3. Dans **Autres opérations**, choisir **« Confirmer l’absence des lignes sélectionnées »**, ou utiliser **Ctrl+Maj+A**.
4. Lire la prévisualisation : elle précise **dans quel témoin** le passage est absent, et combien de groupes automatiques seraient affectés. Confirmer seulement après vérification philologique.
5. Enregistrer le `.vsynch`.

La sélection de plusieurs segments non contigus crée des **groupes d’absence distincts**, et non un groupe englobant artificiellement tout l’intervalle.

### Si la ligne était déjà intégrée à une proposition automatique

Le logiciel peut détacher uniquement les lignes sélectionnées **d’une proposition automatique encore incertaine** ; les autres membres du groupe restent proposés, non validés et révisables. Si cette opération vide entièrement un côté d’une proposition, le groupe automatique est supprimé ; les lignes opposées redeviennent libres. Le programme ne leur attribue **aucune absence implicite**.

Une association manuelle, une correction humaine, une association validée ou une absence déjà confirmée demeure protégée. Pour changer cette décision, **dissocier explicitement** les lignes ou retirer le groupe, puis confirmer la nouvelle absence.

### Retirer une absence

Dans la file de révision, sélectionner le filtre **Absences**, choisir les groupes souhaités, puis utiliser **Autres opérations → Retirer les absences sélectionnées dans la liste**. Une confirmation est demandée. Les lignes concernées redeviennent *non synchronisées* ; aucune autre correspondance n’est créée automatiquement.

### Contrôles de sécurité

- Un aperçu ne modifie jamais le projet.
- Le commit est transactionnel : si l’une des lignes ou associations a changé depuis la prévisualisation, **aucune** modification partielle n’est appliquée.
- Les lignes ignorées, les groupes protégés et les données ALTO/PAGE devenues périmées sont refusés.
- L’opération n’altère ni les images, ni les fichiers ALTO/PAGE, ni les identifiants de lignes physiques.
- Le `.vsynch` conserve `kind: absence`, `state: validated`, la paire de témoins et la preuve de confirmation humaine dans `evidence`.

## Export vers Varians

Une absence confirmée **ne crée pas de `base_keys`** : il n’existe précisément aucune correspondance textuelle à enregistrer. Les autres `base_keys` restent inchangées. Le fichier `rapport_export.json` distingue désormais le nombre de groupes d’absence et le nombre de lignes dont le texte n’a pas d’équivalent, selon le témoin de base choisi.

**Limite du format Varians actuel** : les JSON de synchronisation reflètent les correspondances matérielles, mais ne transmettent pas encore les métadonnées philologiques d’absence sous forme d’un statut explicitement interprété par Varians. Ces décisions sont conservées sans perte dans le projet `.vsynch`.

## Tests

La suite `tests/test_confirmed_exceptions.py` couvre les absences sur un ou plusieurs folios, les absences distinctes dans les deux directions, les groupes automatiques partiellement élagués, la protection des liens validés/manuels, les sélections ignorées, la prévisualisation périmée, les sauvegardes et l’export JSON.
