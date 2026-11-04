# Export direct des alignements vers Varians 0.8.5.2

## Contrat vérifié

Varians lit un JSON par témoin de forme :

```json
{"meta":{"format":"tei-manuscript-alignment","format_version":1,"witness":"F","base_witness":"Mu","role":"secondary"},"pages":[{"id":"identifiant-page","alto_width":4000,"alto_height":5519,"image":{"type":"iiif","service":"https://…","iiif_version":2},"lines":[{"line":1,"order":1,"bbox":{"hpos":100,"vpos":100,"width":250,"height":40},"base_keys":["identifiant-folio-Mu::10"]}]}]}
```

Le témoin de base contient ses lignes physiques, chaque témoin secondaire indique les `base_keys` vers les lignes de ce témoin de base. Cette structure a été contrôlée avec les fonctions `resource_state.synchronization_state` et `image_sources.page_image_source` du code source **Varians 0.8.5.2** remis par l'utilisateur. Les sorties contiennent aussi les polygones PAGE lorsqu'ils sont disponibles.

## Exporter depuis l'interface

Dans « 3 · Synchronisation », choisir **Exporter JSON pour Varians…** puis sélectionner :

1. Le **témoin de référence physique** (provisoire, par exemple Mu).
2. Un **dossier vide**, pour ne pas écraser un export précédent.

Le logiciel y crée :

- `validated/<sigle>.json` : uniquement les associations **validées** ;
- `working/<sigle>.json` : les associations validées **et les propositions incertaines** ;
- `rapport_export.json` : comptes, contrôles et avertissements.

Dans chaque dossier, un JSON est produit pour **chacun** des témoins, y compris la référence physique. Les fichiers représentent uniquement les folios auxquels des ALTO/PAGE ont été associés, pas des centaines de canvases d'un Manifest sans OCR.

Les lignes ignorées restent présentes physiquement, marquées `vsynch_ignored`, mais ne reçoivent pas de correspondance. Ce champ supplémentaire est informatif et n'est pas utilisé comme un statut spécial par Varians.

Les groupes périmés sont exclus, sauf si une équivalence ALTO↔PAGE est **démontrée** par le même UUID PERO, un enregistrement historique dont l'empreinte correspond, et un texte et des coordonnées inchangés. Aucun rapprochement par simple ordre de ligne n'est autorisé lors de cette récupération.

## Point bloquant pour la synchronisation *texte TEI ↔ images*

**Le format JSON est accepté par Varians, mais le contenu ne représente pas encore automatiquement une correspondance avec les `<lb/>` d'une transcription TEI.**

Varians-Synchro peut synchroniser deux manuscrits alors qu'aucune TEI n'existe. L'export utilise donc provisoirement des clés **physiques** comme `UUID-page::12`. Pour que les commandes de synchronisation entre la *transcription éditée* et les témoins soient fiables, il faut :

1. désigner le futur témoin de base éditorial ;
2. associer les lignes `<lb/>` réelles de sa TEI aux lignes physiques de ce témoin ;
3. transférer / normaliser les `base_keys` à partir de cette correspondance et contrôler les ruptures ;
4. importer ensuite les JSON dans le projet Varians.

**Ne pas** fabriquer une TEI fictive à partir de la seule HTR, ni supposer que les 332 lignes de Mu correspondent à 332 balises `<lb/>` d'une édition encore absente. La liste `validated` ne garantit pas non plus automatiquement la justesse philologique des lignes si les données ont été modifiées après validation.

Une fois cette étape établie, dans Varians : **Fichier → Paramètres du projet → Témoins → Modifier → Fichier de synchronisation**, sélectionner le JSON du témoin. Choisir la politique d'images (locales ou IIIF), et conserver les images et fichiers d'origine à leur emplacement ou les recopier dans le projet.

## Export en ligne de commande multiplateforme

```bash
python exporter_json_varians.py projetTest.vsynch --base Mu --output nouveau_dossier_vide
```

Sans PySide6. N'altère ni le `.vsynch`, ni les images, ni les fichiers PAGE/ALTO.

## Limites

- Pas de conversion TEI automatique tant qu'une véritable TEI et sa structure `<lb/>` ne sont pas fournies.
- Pas de transitivité déduite automatiquement des sessions Mu↔F, Mu↔A et F↔A.
- Varians 0.8.5.2 ne connaît pas les statuts `.vsynch` : pour éviter de confondre validé et incertain, importer **un seul ensemble**, en connaissance de son niveau de fiabilité.
- Les chemins d'images locales sont conservés tels qu'indiqués dans le projet source. Sous macOS/Linux ou sur un autre ordinateur, configurer les chemins/ressources d'images dans Varians.
- Lorsqu'une nouvelle segmentation modifie l'ordre ou l'identité des lignes, arrêter l'export des groupes concernés et reprendre la vérification des correspondances.
