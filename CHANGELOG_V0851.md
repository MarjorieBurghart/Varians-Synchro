# Varians-Synchro V0.8.5.1 — ergonomie et finalisation

Cette livraison part intégralement de la V0.8.5 (candidate stable) ; **le moteur d’alignement V0.7.4, les structures `.vsynch`, la liaison TEI ↔ lignes physiques et les exports JSON ne sont pas modifiés**.

## 1. Ajout des témoins

- Étape renommée « 1 · Ajout des témoins ».
- Fiche : « Description : », « Définir ce témoin comme pivot pour l’alignement des témoins », « Supprimer » pour les seules nouvelles ressources.
- Infobulles sur les principales commandes de création/édition, FR/EN.

## 2. Associer les ressources

- Étape renommée « 2 · Associer les ressources ».
- Nouveau titre et aide pédagogique, centrés sur images / ALTO/PAGE / TEI.
- Quatre commandes remontées au-dessus du bilan des témoins, sur deux rangées ; infobulles bilingues.
- « Gérer les images, leur ordre et les associations ALTO/PAGE… ».
- « Définir les lignes à ignorer sur les images du témoin… ».
- « Lier l’édition TEI aux lignes ALTO/PAGE… ».
- Téléchargement **des seuls Canvas IIIF sélectionnés** depuis la fenêtre de gestion des pages, à leur taille native selon l’Image API v2 ou v3 (`full/full` / `full/max`). Images JPEG et index `images.json` publiés ensemble dans un dossier vide, sans altérer les ressources ni la sélection persistée. Téléchargement dans un QThread et annulation explicite ; taille limitée à 160 Mo par fichier. Les Canvas sans service Image API ne peuvent pas utiliser cette commande.

## 3. Aligner les témoins

- Étape et commande renommées « 3 · Aligner les témoins » / « Aligner les témoins ».
- Description sous le titre de la synchronisation par paires avec pivot ; les relations entre deux secondaires s’établissent *via le pivot*, sans création de liens directs n↔m inventés.

## 4. Finaliser

- Étape renommée « 4 · Finaliser ».
- Anciennes informations obscures « Sessions physiques / Sessions TEI héritées » remplacées par « Alignements entre témoins » et un historique TEI uniquement lorsqu’il existe.
- « Contrôler la cohérence du projet… » explique maintenant son périmètre en infobulle et affiche les principales catégories d’erreurs en français/anglais : lignes manquantes, doublons, repères contradictoires, périmètres, ressources externes indisponibles, liens TEI périmés, références `base_keys` exportables. **Contrôle en lecture seule, sans correction automatique**.
- L’export JSON `validated`/`working` est déplacé dans « Finaliser ».
- Nouvelle commande « Créer un projet Varians pré-renseigné… » : écrit `project.xml`, copie la TEI du pivot sous `xml/edition.xml`, produit les JSON validés sous `alignments/`, déclare témoins, images locales ou un Manifest IIIF par témoin et les ALTO/PAGE. Ne modifie aucun fichier source ; le dossier de sortie doit être vide. Les images locales et XML originaux restent des ressources externes référencées par chemin ; ils ne sont pas copiés.
- **Limite importante :** le format `project.xml` a été validé par le parseur de Varians V0.8.5.6 disponible comme référence, mais la compatibilité avec les versions plus récentes de Varians doit être testée par l’utilisateur. L’export physique ne certifie pas à lui seul une correspondance TEI `<lb/>` dans Varians. Si plusieurs Manifests ou sources mixtes existent pour un même témoin, l’export demande un traitement spécifique et refuse de perdre silencieusement des ressources.

## Tests et garanties

- 305 tests Python réussis, 11 tests Qt ignorés faute de PySide6 ici.
- Comparaison des exports sur `projetTest.vsynch` et `test081.vsynch` : empreintes JSON strictement identiques entre V0.8.5 et V0.8.5.1, modes validé et travail.
- Fichier de projet Varians créé et chargé avec succès par le parseur `project_config.load_project` de la référence V0.8.5.6, sans test graphique sur Windows.
- Nouveaux tests sur la sélection IIIF HD, les téléchargements invalides et annulés, la sortie transactionnelle, le projet Varians, les traductions et la disposition du GUI.
