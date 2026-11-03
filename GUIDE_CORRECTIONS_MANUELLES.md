# Corriger une correspondance entre les témoins — V0.6.10

Les images et les fichiers ALTO restent inchangés : les modifications portent exclusivement sur les associations de lignes sauvegardées dans le projet `.vsynch`.

## 1. Une ligne oubliée appartient à un groupe déjà synchronisé

Exemple : la ligne A:17 correspond à B:20 **et B:21**, mais seule B:20 avait été associée.

1. Dans la fenêtre de synchronisation visuelle, cliquez sur **A:17** (déjà synchronisée). La ligne correspondante B:20 est signalée en rose, **sans être sélectionnée pour l'édition**.
2. Cliquez ensuite sur la ligne **B:21** qui avait été oubliée. Il faut que A:17 reste **orange** dans son panneau et B:21 soit **orange** dans l'autre. Les lignes roses ne sont pas sélectionnées automatiquement.
3. Cliquez sur **Associer les lignes** (ou Ctrl+Entrée).
4. Le groupe A:17 ↔ B:20 devient **A:17 ↔ B:20–21**. Le groupe conserve son identifiant dans `.vsynch` ; aucun autre groupe n'est supprimé.

L'opération fonctionne aussi si le groupe initial comporte plusieurs lignes de chaque côté (2↔2 devenant 2↔3, par exemple). Les nouvelles lignes sont rangées par ordre documentaire stable. Une ligne déjà associée à **un autre groupe** ne peut pas être ajoutée sans dissociation explicite : l'outil refuse d'assembler silencieusement des groupes qui seraient peut-être différents.

Si le groupe initial était une **proposition automatique incertaine**, il reste *incertain* après la correction : ajouter une ligne manuellement ne revient pas à valider les autres. Il devient toutefois **protégé contre un futur recalcul automatique**, puisqu'il a été révisé par l'éditeur.

## 2. Dissocier une ligne précise

1. Cliquez sur la ou les **lignes orange** à dissocier, directement sur les images (Ctrl/Maj pour en choisir plusieurs).
2. Cliquez sur **Dissocier**, dans la barre supérieure. L'action est également disponible dans **Autres opérations → Dissocier les lignes sélectionnées**.
3. Seules les lignes sélectionnées sont retirées. Si une correspondance valable subsiste des deux côtés, le groupe est **conservé**. Exemple : A:17 ↔ B:20–21–22, puis dissociation de B:22 ⇒ A:17 ↔ B:20–21.
4. Si un côté devient vide, le groupe est supprimé entièrement et les autres lignes redeviennent libres, **sans création automatique d'une “absence confirmée”**.

L'édition de lignes fonctionne aussi depuis l'onglet textuel facultatif. Les lignes roses servant uniquement à consulter une correspondance ne sont pas affectées.

## 3. Supprimer un groupe entier

Pour effacer toutes les lignes d'une correspondance d'un seul coup, **sélectionnez le ou les groupes dans la liste sous les deux images**, puis utilisez **Autres opérations → Supprimer le(s) groupe(s) sélectionné(s) dans la liste**. Une confirmation vous sera demandée. Cela ne remplace pas la commande « Dissocier » de la barre supérieure, qui agit sur les lignes sélectionnées.

## 4. Réparer les petits trous après interpolation géométrique

Une zone de quelques lignes peut rester non synchronisée lorsque le logiciel n'a pas assez d'éléments pour déterminer s'il s'agit d'un décalage de segmentation, d'une omission ou d'un passage vraiment différent. Avec V0.6.10, un groupe voisin peut être **étendu manuellement sans le détruire**. Par exemple, une ligne du témoin B dont le texte commence à la fin d'une ligne du témoin A et continue au début de la suivante peut donner un lien 2↔1.

L'interpolation n'assimile pas automatiquement une ligne laissée libre à une absence ni ne force son ajout à un groupe validé. Cela resterait une conjecture philologique. Les propositions automatiques non validées peuvent toutefois être recalculées avec « Compléter entre ancrages » sans écraser les corrections humaines.

## 5. Vérifications et sécurité

- Avant les premiers essais, **enregistrer une copie de sauvegarde du projet `.vsynch`**.
- **Les liens manuels/validés ne sont jamais modifiés par un recalcul automatique**.
- Les erreurs (par exemple deux groupes sélectionnés incompatibles) n'entraînent **aucune modification partielle**.
- Les corrections manuelles sont consignées dans `evidence.manual_corrections`, avec date, lignes ajoutées ou retirées et provenance antérieure.
- L'état initial « incertain » est conservé s'il était incertain ; « validé » est conservé si la correction est apportée par l'utilisateur à un lien déjà validé.
- Pour enregistrer sur disque, fermer la fenêtre de synchronisation puis choisir **Enregistrer** dans la fenêtre principale.

Les commandes et les messages correspondants disposent de traductions française et anglaise dans `i18n/fr.xml` et `i18n/en.xml`.
