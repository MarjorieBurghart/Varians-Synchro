# Varians-Synchro V0.8.4.2 — Sélection visuelle prévisible

## Fonctionnalités corrigées

- « Repères discrets » **désactivé à l'ouverture**, y compris pour les fichiers ALTO rectangulaires. L'option reste activable à tout moment par l'utilisateur et n'est plus imposée lors du chargement d'une page.
- Dans la synchronisation visuelle entre deux témoins, **clic simple** : remplace toutes les lignes précédemment sélectionnées dans le témoin concerné, sur le même folio **et sur les autres folios**.
- **Ctrl+clic** : ajoute ou retire individuellement la ligne visée, sans affecter les autres.
- **Maj+clic** : sélectionne l'intervalle inclusif entre le dernier point d'ancrage et la ligne cliquée, dans l'ordre documentaire de lecture (y compris d'un folio à un autre).
- **Ctrl+Maj+clic** : ajoute cet intervalle à la sélection existante.
- Les clics dans la liste de lignes (HTR/TEI facultative) et directement sur le manuscrit appliquent les mêmes règles.
- Le panneau opposé montre en rose les **correspondances de toute la sélection actuelle**, mais ne les sélectionne jamais ; un clic simple remplace l'ancienne prévisualisation, et « Désélectionner » la vide.
- L'ordre de lecture est mis en cache pour éviter de reparcourir tous les PAGE/ALTO à chaque clic.

## Protections

Ce changement ne modifie aucun fichier projet `.vsynch`, aucun groupe d'alignement, aucune ligne physique, ni l'algorithme textuel V0.7.4 et les exports JSON destinés à Varians. Les raccourcis Ctrl/Maj ne concernent que la sélection temporaire de l'interface.

## Vérifications

- Tests unitaires sans Qt : clic simple, Ctrl, Maj, Ctrl+Maj, changement de folio, indépendance des témoins, cumul et suppression des surlignages de correspondances.
- Tests PySide6 additionnels pour la sélection dans l'image et dans la liste, et le réglage « Repères discrets » (non exécutés dans l'environnement de construction sans PySide6).
- Tests de non-régression existants.

Lire aussi `TESTS_V0842.md`.
