# Varians-Synchro 0.7.1 — Synchroniser par progression du passage

## Principe

**Deux correspondances validées délimitent un même passage, quelles que soient les différences de mise en page.** Varians-Synchro rassemble toutes les lignes physiques actives dans l'ordre de lecture, même lorsqu'elles traversent plusieurs colonnes ou plusieurs folios. Les changements de page ne constituent plus des barrières.

Le moteur `varians_synchro/textual_progress.py` propose une répartition monotone des deux flux entre les repères. La proposition ne vérifie pas l'identité philologique des textes. Le contenu HTR, très imparfait sur les manuscrits, sert **uniquement à estimer une quantité de signes**, pas à établir une correspondance de mots.

## Mode d'emploi

1. Ouvrir une **copie de travail** du `.vsynch` existant dans la V0.7.1.
2. Vérifier l'ordre des folios et colonnes via **Autres opérations → Ordre de lecture et intervalles…**. Corriger l'ordre si nécessaire.
3. Poser ou valider **deux groupes de correspondance homologues**, début et fin de passage. Un groupe 1↔n ou n↔m validé convient comme repère.
4. Dans l'alignement visuel, cliquer **Synchroniser entre repères (texte)**. Une fenêtre présente les propositions et les anomalies éventuelles. Les nombres avant et après les transitions de folios appartiennent au même flux.
5. Examiner les propositions, en désélectionner si nécessaire, puis cliquer **Enregistrer la sélection**. Les anciennes propositions **automatiques et incertaines** recouvertes peuvent être remplacées après une confirmation explicite. Les groupes manuels et validés restent intacts.
6. Vérifier visuellement les groupes proposés (**incertains**), corriger les segmentation 1↔n / n↔m si nécessaire, puis **valider** les correspondances fiables. Enregistrer le `.vsynch` et exporter les JSON pour Varians comme auparavant.

**Attention à la commande ancienne :** les anciennes interpolations géométrique et résiduelle sont déplacées sous **Autres opérations**, avec la mention « compatibilité ». Pour cette refonte, utiliser le nouveau bouton principal.

## Algorithme utilisé

Pour chaque intervalle homogène entre repères :

- Chaque ligne reçoit un poids positif. Priorité à la **longueur HTR** (nombre de lettres/chiffres, sans comparaison lexicale), avec garde-fous contre les résultats OCR manifestement aberrants ; sinon **longueur de la ligne de base PAGE ou largeur du rectangle ALTO/PAGE**, calibrée avec les textes disponibles dans le témoin ; enfin **poids uniforme**.
- Les poids sont convertis en progressions cumulées de 0 à 100 % *séparément dans chaque témoin*. Aucune comparaison des pixels absolus des deux manuscrits n'intervient.
- Le témoin comportant le moins de lignes sert de séquence pivot pour rechercher les coupures cumulées les plus proches. Les groupes proposés sont **1↔n ou n↔1**, dans l'ordre, sans plafond arbitraire de lignes et sans critère de rapport 3:1. Les **groupes n↔m** restent intégralement pris en charge pour les repères validés et les corrections manuelles ; une production automatique optimisée de tels regroupements est un perfectionnement possible.
- Le calcul n'altère pas les associations éditoriales protégées : toute association manuelle encore incertaine est une barrière. Les groupes protégés internes découpent les grands passages en sous-intervalles indépendants.
- Les lignes explicitement ignorées n'entrent jamais dans les calculs. Une **absence** confirmée d'un côté réserve les lignes concernées : elle n'est pas déduite automatiquement.

## Pourquoi des lignes peuvent-elles rester libres ?

**Il n'y a pas de repère à leurs deux extrémités.** L'algorithme ne devine pas les limites d'un passage. Un diagnostic spécial signale les lignes libres avant le premier repère ou après le dernier repère.

**Il ne reste des lignes que d'un côté de la paire.** Cela peut signaler une omission, une différence de découpage à corriger par extension manuelle d'un groupe protégé, ou un repère inapproprié. Le logiciel n'invente pas d'absence.

**Deux repères se contredisent ou traversent une association protégée.** Le calcul passe les autres intervalles indépendants, signale l'exception et ne touche pas aux groupes responsables. L'inspecteur d'ordre aide à corriger les repères.

**Une sélection partielle ne peut pas remplacer intégralement un ancien groupe automatique.** Dans ce cas, l'écriture atomique ignore la proposition problématique : une demi-réécriture qui perd des membres serait dangereuse.

## Résultat constaté sur le projet Mu–F de référence

Sur le `.vsynch` fourni lors du développement : Mu **211 lignes actives**, F **241**. Le moteur construit **140 groupes incertains**, avec **142 lignes Mu** et **154 lignes F** dans les intervalles exploitables, en ~**29 ms** pour le calcul dans l'environnement de test. Le statut des 60 groupes validés ne change pas. Les 17 lignes libres de F sont situées **après le dernier repère** (folio 16v, lignes 2 à 18) et ne peuvent donc pas être traitées entre deux repères : vérifier leur appartenance au texte édité.

La contradiction déjà connue Mu 4r:25→F 16r:32 puis Mu 4r:26→F 16r:31 reste signalée, sans révision silencieuse.

L'export JSON *validé seulement* avant/après recalcul est inchangé sur le projet test. L'export *travail* reflète légitimement les propositions recalculées après leur acceptation. Aucun lien ni fichier du projet original n'a été modifié lors des essais.

## Conditions de validation

- Commande de tests : `python -m pytest -q` depuis la racine du logiciel.
- Les tests graphiques PySide6 sont à exécuter sur un ordinateur avec Qt installé ; les tests métiers sont autonomes.
- Les performances mesurées concernent **le calcul**, sans chargement d'images IIIF.
- Une proposition incertaine ne doit jamais être considérée comme une transcription ni comme un jugement philologique.
