# V0.6.6 — Consulter la ligne correspondante dans l’autre manuscrit

1. Dans **Synchronisation visuelle**, cliquez sur une ligne déjà liée (cadre vert ou bleu) dans l’un des deux manuscrits.
2. Dans l’autre manuscrit, sa ou ses correspondantes apparaissent **en rose**. Si elles se trouvent sur un autre folio, la page correspondante est ouverte automatiquement et recentrée (après chargement de l’image).
3. Un clic depuis le second manuscrit fonctionne dans le sens inverse. Les groupes de lignes 1↔n et n↔m sont respectés.
4. Le **rose est une indication visuelle temporaire, pas une sélection** pour créer un alignement. Seul le **orange** désigne la sélection de travail. Les lignes roses restent visibles même avec un filtre d’affichage restrictif.
5. Une absence confirmée ne désigne aucune ligne dans l’autre manuscrit ; la barre d’état signale ce cas. Cliquer une ligne non liée efface l’ancien surlignage.
6. Double-cliquer sur une association de la liste du bas montre aussi les deux groupes en rose, sans modifier la sélection de travail.

**Attention :** pour associer deux nouvelles lignes, il faut toujours les sélectionner explicitement sur chacune des deux images. Un clic sur une ligne liée ne crée ou valide aucun nouveau lien.

---

# Nouveauté V0.6.5 — Cadres visibles

Un sélecteur placé juste au-dessus des deux images permet de filtrer l’affichage des **cadres ALTO** :

1. **Toutes les lignes** : tous les rectangles ALTO, avec leurs couleurs de statut.
2. **Lignes non synchronisées** : uniquement les lignes sans aucun lien dans la **session entre les deux témoins affichés**.
3. **Synchronisations automatiques à vérifier** : uniquement les correspondances suggérées automatiquement (HTR–HTR ou géométrie) qui ne sont pas encore validées.

**Important** : les filtres n’effacent pas les correspondances ; seule la visibilité des rectangles change. Les lignes actuellement sélectionnées restent visibles en **orange**, pour ne pas interrompre une manipulation. Revenir à **Toutes les lignes** pour tout afficher.

Les associations automatiques incertaines sont **bleues et pointillées** ; elles deviennent bleues et pleines lorsqu'elles sont validées. Les associations manuelles sont vertes. Une absence déclarée est signalée par un cadre rouge pointillé en vue complète.

---

# Guide pratique : compléter les lignes entre les ancrages

## Exemple courant

Vous avez importé deux témoins (images locales ou IIIF) et associé leurs ALTO aux pages concernées. Vous avez établi uniquement les correspondances entre la **première** et la **dernière** ligne de chaque **colonne** du manuscrit pivot et les lignes correspondantes du second témoin.

1. Ouvrez le projet `.vsynch` dans Varians-Synchro.
2. Dans **3 · Synchronisation**, choisissez le **pivot technique** et le **témoin à aligner**, puis ouvrez l'alignement visuel.
3. Vérifiez que les associations des extrémités de chaque colonne figurent dans la liste et qu'elles sont **validées**. Une association manuelle est validée par défaut ; les propositions automatiques, non.
4. Cliquez sur **Compléter entre ancrages (géométrie)**, toujours en **haut** de la fenêtre, à côté de **Associer les lignes**.
5. Le logiciel cherche les intervalles encadrés par deux ancrages 1↔1, sur une seule page et une seule colonne de chacun des deux témoins. Il utilise la hauteur relative des lignes, leur ordre et une éventuelle similitude HTR comme indice secondaire.
6. Dans la prévisualisation, vérifiez les correspondances proposées, désélectionnez si besoin les groupes trompeurs, puis cliquez sur **Enregistrer les propositions sélectionnées**.
7. Les nouvelles associations sont **incertaines**. Parcourez les images, corrigez les zones douteuses, puis **validez** les correspondances correctes depuis **Autres opérations → Valider sélection**.
8. Revenez à la fenêtre principale et cliquez sur **Enregistrer**. Les modifications du projet ne sont pas sauvegardées automatiquement sur disque.

## Important

- Deux ancrages ne suffisent pas toujours : dès qu'une colonne comporte une addition, une lacune ou un ordre de lecture différent, ajoutez des ancrages intermédiaires.
- Aucune conclusion philologique n'est tirée de l'absence de correspondance. Le programme ne déclare pas une omission automatiquement.
- Le calcul ne franchit pas aveuglément les limites de page/colonne ; consultez les avertissements si un intervalle a été ignoré.
- Les lignes ALTO elles-mêmes doivent être définies dans un ordre de lecture cohérent (notamment dans les manuscrits à plusieurs colonnes). Une inversion pourra empêcher le calcul plutôt que créer une association mensongère.
- Le score produit est **un indice de cohérence géométrique**, non une probabilité de justesse.
- Une HTR très mauvaise peut être totalement ignorée ; la méthode reste disponible sans texte HTR.
- L'algorithme limite la taille des groupes estimés et ne couvre pas encore tous les changements de structure du texte.

## Petits écrans et clavier

Les commandes essentielles se trouvent en haut de la fenêtre. L'interface est dimensionnée selon la zone disponible, et le reste des opérations se trouve dans **Autres opérations**. **Ctrl+Entrée** crée une association avec les lignes sélectionnées. Zoom à la molette, double-clic pour agrandir une ligne, Ctrl/Maj pour sélectionner plusieurs cadres.

## English interface

Select **English** from **Langue / Language** in the main window. The language selection persists across application restarts. The `.vsynch` project format and the manuscript data are unaffected.

## V0.6.3 — Redonner la place aux images

Dans **chaque** panneau de manuscrit, la case **Texte HTR** agit sur la visibilité du panneau complet, et pas seulement sur le contenu textuel :

- **Texte HTR décoché** (par défaut) : la liste sous l'image est entièrement masquée et l'image utilise l'espace vertical libéré.
- **Texte HTR coché** : la liste revient sous l'image. Déplacer la poignée du séparateur entre image et texte pour ajuster librement la hauteur de la liste.
- Les cadres ALTO restent cliquables dans les deux situations ; les sélections, le zoom et les ancrages sont conservés.
- **Effacer sélection** reste dans la rangée de commandes visible au-dessus de l'image même lorsque l'HTR est masquée.
- Les deux panneaux (témoin de référence et témoin comparé) possèdent chacun leur case et fonctionnent indépendamment.

La vue textuelle séparée demeure facultative et inchangée.


## V0.6.12 : lignes obliques et polygones PERO

Si les cadres ALTO se chevauchent alors que PERO affiche des contours inclinés corrects, vérifiez le statut sous l'image : « contours polygonaux ALTO » indique que les `Shape/Polygon` ont été retrouvés. Varians-Synchro dessine désormais ces contours et les utilise pour départager les clics. En absence de polygones, les rectangles englobants sont utilisés et les repères compacts sont recommandés. Les données de synchronisation ne sont jamais changées par le choix d'affichage.
