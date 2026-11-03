# Contrôle et complétion des lignes résiduelles (V0.6.14)

## Pourquoi ce second passage ?

Lorsque le découpage des lignes diffère entre deux manuscrits, une ligne peut rester isolée d'un côté alors que le passage correspondant est déjà inclus dans un groupe de l'autre. Le calcul par intervalles de la V0.6.13 ne peut alors plus constituer de paire libre.

## Utilisation

1. Placer des ancrages fiables aux extrémités des colonnes ; lancer **« Compléter entre ancrages (géométrie) »** et enregistrer les propositions souhaitées.
2. Dans la fenêtre d'alignement visuel, choisir **« Compléter les lignes restantes… »** à côté de « Cadres visibles » ou dans « Autres opérations ».
3. Examiner chaque proposition : elle indique les lignes encore libres et le groupe existant qui serait agrandi. Les propositions sont incertaines : leur seule proximité n'atteste pas une correspondance textuelle.
4. Désélectionner toute proposition douteuse ; confirmer avant l'enregistrement.
5. Revenir aux images : l'extension reste **bleue pointillée** jusqu'à validation. Cliquer sur ses lignes pour naviguer dans l'autre témoin et vérifier le passage.
6. Sauvegarder le `.vsynch`.

## Cas non modifiés automatiquement

- Ancrages manuels et tout groupe validé : utiliser la commande manuelle « Associer les lignes » pour ajouter une ligne à un tel groupe.
- Correspondance possible entre deux lignes encore libres : relancer l'interpolation normale plutôt que d'absorber ces lignes dans des groupes voisins.
- Lignes ignorées, folios distincts, colonnes non concordantes, distances trop grandes ou situation géométriquement ambiguë.
- Absence confirmée : ne jamais la déduire d'une seule lacune de synchronisation.

## Sécurité

La prévisualisation ne modifie rien. Un projet dont les lignes ou les groupes auraient changé entre la prévisualisation et l'enregistrement doit être recalculé. La mise à jour est atomique, et les fichiers PAGE, ALTO et les images ne sont jamais réécrits.

Le diagnostic donne des comptages des causes de non-proposition. Ces chiffres peuvent comptabiliser plusieurs hypothèses refusées pour une même zone ; ce ne sont pas des statistiques de certitude philologique.
