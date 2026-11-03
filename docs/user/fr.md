# Guide utilisateur — Varians-Synchro V0.8.5.5

Varians-Synchro aligne les lignes physiques de témoins manuscrits à partir d’images et de segmentations ALTO/PAGE. Il prépare des correspondances utilisables dans Varians sans modifier les sources.

> ALTO / PAGE-XML / IIIF / TEI / HTR / `.vsynch` / `base_keys`: technical identifiers and original manuscript text are never translated.

## Installer et démarrer

Utiliser Python avec PySide6 installé. Sous Windows, lancer start_windows.bat ou run.py. Avec Spyder, préférer le processus séparé décrit dans GUIDE_DEPANNAGE_SPYDER.md.

## Créer le projet et les témoins

Choisir Nouveau projet et enregistrer immédiatement le fichier .vsynch. Ajouter chaque témoin avec son sigle, ses images locales ou son Manifest IIIF, ses fichiers ALTO/PAGE et, facultativement, une édition TEI XML. Désigner le témoin pivot pour les correspondances.

## Associer les ressources

Dans 2 · Associer les ressources, vérifier l’ordre naturel des images et les propositions images ↔ ALTO/PAGE. Le rapprochement par nom est prioritaire ; l’ordre naturel n’est qu’une proposition à confirmer. Les Canvas sans segmentation peuvent rester sans association.

## Définir le périmètre

Marquer les lignes hors édition comme ignorées, notamment les lignes précédant le début et suivant la fin d’un passage. Les pages peuvent traverser plusieurs folios.

## Lier la TEI

La TEI doit comprendre des <lb edRef="#SIGLE"/> attribués au témoin. Vérifier le nombre de lignes TEI et de lignes physiques actives ; contrôler le texte et le recadrage manuscrit, initialement la première ligne, puis toute ligne choisie, avant de confirmer. Les apparats ambigus bloquent la liaison automatique.

## Aligner deux témoins

Dans 3 · Aligner les témoins, choisir une paire de témoins, établir des repères homologues, demander des propositions de progression textuelle, puis les revoir. Clic simple = remplacer la sélection du témoin entier ; Ctrl+clic = ajouter/retirer ; Maj+clic = plage. Les correspondances consultées sur l’autre témoin ne sont pas des sélections.

## Valider et traiter les absences

Valider les groupes corrects ; corriger les groupes incertains. Les absences confirmées sont propres à la paire, alors que les lignes ignorées sont hors périmètre du témoin. Les groupes manuels ou validés sont protégés des recalculs automatiques.

## Nouvelle segmentation d’une page

Donner à une page un autre fichier ALTO/PAGE (segmentation corrigée) peut changer ses lignes : une ligne est repérée par son rang dans la page. Avant le remplacement, Varians-Synchro indique combien de groupes citent ces lignes. Après confirmation, les groupes dont les lignes ont changé sont marqués « [périmé] » : ils ne sont plus utilisés comme repères, ni dans les calculs, ni dans l’export, mais ne sont jamais supprimés. Le filtre « Périmés » de la fenêtre d’alignement les liste ; après vérification sur les images, « Revalider… » les rétablit, sinon dissociez-les. L’ordre de lecture corrigé de la page est remis à zéro.

## Images IIIF HD et HTR

Télécharger uniquement les Canvas HD utiles. Enregistrer ensuite le projet : les lots et les références Canvas sont conservés. Le projet Varians n’utilise ces copies locales que si toutes les pages nécessaires avec ALTO/PAGE sont couvertes et intègres. Les commandes Exporter pour HTR / Réimporter HTR servent à un traitement de reconnaissance externe ; elles sont facultatives.

## Finaliser et exporter

Dans 4 · Finaliser, lancer le contrôle de cohérence (lecture seule). Exporter les JSON validated (liens validés) et working (liens validés + propositions) ou créer un dossier Varians pré-renseigné. Vérifier les avertissements avant import dans Varians.

## Sauvegardes et résolution de problèmes

Le .vsynch est sauvegardé atomiquement, avec une copie précédente .vsynch.bak. Faire des copies avant de changer le périmètre ou les sources. Une image IIIF indisponible ne signifie pas que les associations sont perdues. Vérifier les chemins locaux, les accès réseau et les diagnostics.

---

## Technical references

- `GUIDE_COPIES_HD_V0853.md`
- `GUIDE_LIAISON_TEI_V083.md`
- `GUIDE_REVISION_RAPIDE.md`
- `GUIDE_SAUVEGARDE_V085.md`
