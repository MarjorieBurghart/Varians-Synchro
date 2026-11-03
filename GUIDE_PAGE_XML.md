# Importer et synchroniser avec PAGE-XML ou ALTO

## Formats pris en charge

**ALTO-XML** (racine `alto`) : le texte provient de `String@CONTENT`, les coordonnées de `TextLine@HPOS`, `VPOS`, `WIDTH`, `HEIGHT` et, si présents, de `TextLine/Shape/Polygon`.

**PAGE-XML** (racine `PcGts`) : le texte HTR provient de `TextLine/TextEquiv/Unicode`, les contours exacts de `TextLine/Coords@points` et les dimensions de `Page@imageWidth` et `imageHeight`. L'ordre des régions tient compte de `ReadingOrder/OrderedGroup/RegionRefIndexed` lorsqu'il existe. Les lignes sans contours géométriques utilisables sont signalées et ne deviennent pas de faux rectangles.

Les fichiers PAGE ne doivent pas obligatoirement posséder une HTR : une segmentation seule suffit pour l'association visuelle et les interpolations géométriques. Plusieurs versions du namespace PAGE sont acceptées. Les polygones sont conservés tels quels, dans les coordonnées de l'image source, puis transformés à la résolution affichée.

## Créer un projet

1. Ouvrir `run.py` avec Python/PySide6, puis créer un projet ou ouvrir un `.vsynch`.
2. Dans l'étape **Projet et témoins**, ajouter un témoin ; importer ses images locales ou son Manifest IIIF.
3. Cliquer **Importer ALTO ou PAGE** et choisir les fichiers XML, éventuellement de formats différents. L'application examine la racine du XML, et non son nom.
4. Dans **Pages et ALTO**, ouvrir la gestion des pages. Appliquer les suggestions non ambiguës, ou choisir explicitement un fichier PAGE/ALTO et son numéro de page pour chaque image. L'association n'est pas nécessairement confirmée : contrôler les contours sur l'image.
5. Dans **Synchronisation**, sélectionner les témoins, ouvrir l'alignement visuel et associer les lignes. PAGE et ALTO fonctionnent ensemble dans la même session ; TEI et TXT ne sont pas obligatoires.
6. Enregistrer le `.vsynch` sous un nouveau nom de sauvegarde.

## Pour récupérer les contours de PERO

Exporter un **PAGE-XML avec segmentation des lignes** depuis PERO. Il n'est pas nécessaire d'exporter ALTO en plus si le PAGE contient déjà le texte HTR. Lorsque `TextLine/Coords` est présent, le viewer utilise les polygones réellement enregistrés par le fichier PAGE, au lieu des rectangles englobants ALTO.

Il faut choisir le PAGE comme **source active de cette image** dans le gestionnaire des pages. Le simple fait de l'importer à côté d'un ALTO déjà associé n'active pas ses contours. Le logiciel ne superpose pas automatiquement des lignes provenant de deux segmentations potentiellement différentes.

## Source mixte et fidélité des associations

Un témoin peut comporter des pages localement imagées et des Canvas IIIF, avec un PAGE sur certaines pages et un ALTO sur d'autres. Des témoins PAGE peuvent être alignés avec des témoins ALTO.

**Attention aux projets déjà alignés :** remplacer la source active sur une page peut changer le nombre ou l'ordre des lignes. Les références de correspondance doivent être revérifiées avant validation. Faire une copie du `.vsynch` avant un remplacement massif. Le logiciel ne transforme ni les fichiers images ni les fichiers XML sources.

Si le PAGE-XML comporte des lignes sans `Coords` exploitable, l'importation signale leur nombre. Si un dessin de ligne ne correspond pas à l'image, vérifier les dimensions `Page@imageWidth`/`imageHeight` et l'image véritablement liée à la page (le nom `imageFilename` sert à suggérer une correspondance, pas à garantir sa justesse).

## Limitations de cette version

- Une seule source de segmentation **active par page** ; importation simultanée possible, fusion automatique PAGE/ALTO non implémentée.
- Les TextLine sans `Coords` ne peuvent pas être cliquées ; elles sont comptabilisées dans le diagnostic et omises de l'inventaire alignable.
- Les changements de source pouvant réordonner les lignes nécessitent une relecture des groupes existants.
- L'interface graphique doit être testée sous Windows, macOS et Linux ; les tests automatiques du noyau n'équivalent pas à une validation visuelle sur toutes les plateformes.

