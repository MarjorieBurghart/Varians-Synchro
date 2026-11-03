# Varians-Synchro V0.8.4 — Contrôle visuel TEI et recherche textuelle

## Objet

V0.8.4.1 prolonge la liaison TEI ↔ lignes physiques mise en place en V0.8.3 : la confirmation n'est plus fondée seulement sur des effectifs. **Un seul aperçu (texte TEI + image manuscrite) apparaît à la fois.** La première ligne est sélectionnée à l'ouverture ; l'utilisateur peut passer à la fin ou sélectionner librement une ligne intermédiaire.

Aucune nouvelle association n'est déduite d'une photographie. Le logiciel affiche la *proposition* produite par l'ordre de lecture et conserve l'exigence de confirmation humaine. Deux extrémités correctes n'établissent pas à elles seules la correction de toutes les lignes internes.

## 1. Contrôler le rattachement TEI ↔ ALTO/PAGE

1. Dans **Projet et témoins**, rattacher une édition TEI au témoin souhaité.
2. Associer les images aux ALTO/PAGE et, dans **Pages et ALTO/PAGE**, définir le **périmètre physique du témoin** (lignes ignorées).
3. Dans **Pages et ALTO/PAGE**, cliquer sur **Lier la TEI aux lignes ALTO/PAGE…**.
4. La fenêtre affiche les effectifs, les diagnostics et **la liste complète des lignes TEI** (colonne gauche).
5. Dans la colonne droite, contrôler la **première ligne**, sélectionnée automatiquement : texte TEI, référence physique et photographie recadrée du manuscrit.
6. Cliquer sur **Fin** pour afficher, **à la place de la première image**, la dernière ligne et son texte TEI.
7. Facultativement, rechercher du texte dans la liste de gauche puis **cliquer sur une ligne** pour remplacer le même aperçu par celui de cette ligne. La saisie d'une recherche ne déclenche pas à elle seule de téléchargement IIIF.
8. Cliquer sur **Voir dans le visualiseur…** pour ouvrir la page originale en grand et centrer le contour exact de la ligne sélectionnée.
9. Confirmer la liaison puis **enregistrer le `.vsynch`**.

Le contour de ligne apparaît **en jaune**, sur un recadrage laissant apparaître le contexte immédiat. Les extraits TEI affichés utilisent les lectures de témoin déjà résolues par l'extracteur V0.8.3, non la HTR.

## 2. Images locales, ALTO et PAGE-XML

- Le recadrage utilise le rectangle de la ligne et, s'il est présent, le **polygone exact** de PAGE ou d'ALTO.
- Les proportions sont calculées d'après les dimensions de la segmentation. La sélection du contour n'altère jamais le XML original.
- Les images locales sont chargées en tâche séparée et découpées après décodage ; les images de grande taille peuvent nécessiter plus de mémoire.
- **IIIF Image API v2/v3** : lorsqu'un service et les dimensions du Canvas sont disponibles, le logiciel demande une *région* plutôt que l'image entière ; il tient compte de la différence éventuelle d'échelle entre Canvas et ALTO/PAGE. Sinon il utilise l'adresse image disponible, à résolution limitée lorsqu'un service sait la fournir.
- En cas de coupure réseau ou d'un service IIIF refusant le recadrage, **Aperçu indisponible** est affiché. Si les deux extrémités n'ont pas été effectivement chargées à un moment de cette vérification (avec le panneau unique), une confirmation supplémentaire est demandée avant la validation ; le logiciel ne considère pas la ligne de fin comme contrôlée par défaut.
- Les requêtes d'image ne modifient ni le manifeste IIIF ni le projet.

## 3. Afficher la TEI dans la synchronisation entre témoins

Dans **Synchronisation visuelle entre témoins**, pour un témoin avec une **liaison TEI valide** :

- La vue textuelle secondaire et l'option d'affichage du texte dans le panneau image utilisent désormais le **texte TEI lié**, à la place de la HTR.
- Le bouton « Texte TEI » remplace « Texte HTR » lorsque l'édition liée est utilisable ; l'affichage reste facultatif pour préserver la surface d'image.
- Une **recherche TEI** est accessible depuis le bandeau de la fenêtre de synchronisation. Choisir le témoin, saisir un mot ou un passage, puis Entrée ou **Suivant** : l'image se repositionne sur la ligne correspondante, même sur un autre folio. Plusieurs occurrences peuvent être parcourues.
- En l'absence de liaison valide, la HTR originale continue d'être utilisée comme texte secondaire. Une liaison périmée n'est jamais considérée comme une transcription actuelle.

Les résultats de recherche ne deviennent **pas** des repères ni des correspondances Mu–F–A et ne sont jamais enregistrés comme liens : il s'agit d'une simple navigation visuelle.

## 4. Garanties

- Les fichiers TEI / PAGE / ALTO et les images restent **en lecture seule**.
- Les liaisons éditoriales sont toujours indépendantes des correspondances entre témoins.
- L'ordre physique et la définition des lignes ignorées restent les seuls déterminants des propositions automatiques par rang.
- Les empreintes de TEI et de segmentation sont contrôlées avant validation ; les propositions périmées sont refusées.
- Aucun téléchargement IIIF n'est nécessaire pour calculer les correspondances ; seules les images affichées sont demandées.
- Le moteur de progression textuelle de V0.7.4 et le format de l'export JSON vers Varians restent inchangés.

## 5. Limites et recette sur Windows

Les tests non graphiques valident la géométrie et les données ; **les tests d'interface PySide6 n'ont pas pu être exécutés dans l'environnement de livraison**. Sur Windows/Spyder, vérifier que seule l'image du début charge à l'ouverture, que « Fin » et la sélection d'une ligne remplacent bien cette même image, puis les polygones inclinés, la recherche dans la synchronisation visuelle, la fermeture pendant un chargement IIIF et la validation après une indisponibilité de réseau.

Tester aussi avec des pages dont la résolution IIIF diffère de celle du fichier ALTO/PAGE et au moins une liaison TEI sur plusieurs folios.
