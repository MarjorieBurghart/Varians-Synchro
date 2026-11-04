# Registre raisonné des décisions techniques (ADR)

Un ADR présente **décision / raison / effet / état / sources**. Ce registre reconstruit les motivations à partir du code livré, des notes historiques et du contexte projet ; il ne prétend pas être un compte rendu signé d'architecture. En cas de conflit, examiner le code et les tests de la livraison ainsi que les demandes éditoriales consignées par le responsable du projet.

## ADR-001 — Séparer les correspondances physiques et l'édition TEI

- **Décision** : enregistrer les appariements de lignes de manuscrits dans `pair_sessions`, conserver les anciennes `alignment_sessions`, lier la TEI facultativement dans `text_resources[].tei_binding`.
- **Motivation** : un alignement entre deux témoins doit pouvoir être préparé avant l'édition TEI ; la relation philologique ne se déduit pas du texte HTR.
- **Effet** : deux pistes de provenance indépendantes ; export physique possible sans TEI, export projet Varians complet avec au plus une TEI pivot (sans TEI : TEI vide de Varians, voir ADR-016).
- **État** : implémenté. **Sources** : `physical_alignment.py`, `tei_binding.py`, `varians_export.py`, `FORMAT_PROJET.md`.

## ADR-002 — Choix de pivot et direction de paire distincts

- **Décision** : `pivot_witness_id` est un choix de projet ; `reference_witness_id` et `target_witness_id` sont l'orientation technique de chaque paire ; une paire inversée ne crée pas une seconde session.
- **Motivation** : éviter de transformer un témoin « pivot physique » en texte critique de référence ou de dupliquer des validations.
- **État** : implémenté. **Sources** : `resource_workflow.py`, `physical_alignment.create_pair_session`.

## ADR-003 — Refuser toute transitivité implicite

- **Décision** : aucune correspondance F↔L automatique dérivée des paires F↔Mu et Mu↔L.
- **Motivation** : segmentation et absence peuvent empêcher une bijection ; une déduction est une hypothèse, pas une preuve.
- **État** : implémenté. **Sources** : `varians_export._pair_for_base`, `validation.audit_project`.

## ADR-004 — Sauvegarder atomiquement avec version précédente

- **Décision** : fichier temporaire sur même volume, publication par `os.replace`, backup `.vsynch.bak` des anciens octets uniquement à partir du second enregistrement.
- **Motivation** : prévenir corruption et écrasement des corrections manuelles.
- **État** : implémenté ; une robustesse de crash matériel complète (fsync des répertoires) **n'est pas démontrée**. **Source** : `core.save_project`.

## ADR-005 — Identité physique stable sous segmentation constante

- **Décision** : UID UUIDv5 déterministe sur `[témoin,page,ordinal]` et empreinte du contenu/géométrie.
- **Motivation** : référence durable indépendante de la traduction et de la vue Qt.
- **Limite** : changement d'ordinal / nouvelle segmentation doit déclencher une révision ; même UID n'est pas une preuve de même ligne.
- **État** : implémenté. **Sources** : `physical_alignment.line_uid`, `physical_lines`.

## ADR-006 — Privilégier la vérification humaine sur l'optimisation de couverture

- **Décision** : états proposed/uncertain/validated, preuves de validation, propositions recalculables **seulement** si non protégées, confirmations d'absence et exclusion du périmètre distinctes.
- **Motivation** : les correspondances médiévales ne sont pas nécessairement exactes ligne à ligne.
- **État** : implémenté. **Sources** : `physical_alignment.py`, `exceptions.py`, `line_scope.py`, `review.py`.

## ADR-007 — Conserver le moteur de progression textuelle V0.7.4

- **Décision** : étendre les propositions HTR par progression cumulée entre repères et repli HTR → géométrie régionale → uniforme ; ne pas remplacer les repères croisés par un modèle global.
- **Motivation** : l'HTR incomplet et les colonnes nécessitent une estimation localement calibrée.
- **État** : implémenté ; exactitude à vérifier éditorialement. **Sources** : `textual_progress.py`, `reading_stream.py`, `AUDIT_INTEGRITE_V074.md`.

## ADR-008 — Export distinct « validé » et « travail »

- **Décision** : `validated/` et `working/` toujours clairement séparés, avec rapport et publication en dossier vide.
- **Motivation** : interdire de présenter les hypothèses comme des correspondances confirmées.
- **État** : implémenté. **Sources** : `varians_export.py`, `EXPORT_VARIANS.md`.

## ADR-009 — Conserver ALTO/PAGE et les identifiants historiques

- **Décision** : détection par racine XML ; PAGE polygones, rectangles communs, champ `alto_binding` maintenu pour les deux ; ALTO et PAGE non réécrits.
- **Motivation** : interopérabilité avec corpus et projets enregistrés.
- **État** : implémenté. **Sources** : `core.inspect_line_source`, `page_xml.py`, `alto_geometry.py`, `FORMAT_PROJET.md`.

## ADR-010 — Images HD IIIF en copies optionnelles intègres

- **Décision** : enregistrement par Canvas/URL + SHA-256 ; copies locales exportées uniquement lorsque toutes les pages segmentées du même témoin sont couvertes.
- **Motivation** : un répertoire HD incomplet ne doit pas devenir un « projet hors ligne » trompeur.
- **État** : implémenté. **Sources** : `hd_registry.py`, `varians_project_export.py`, `GUIDE_COPIES_HD_V0853.md`.

## ADR-011 — Qt isolé de Spyder

- **Décision** : lancement dans un sous-processus lorsqu'un noyau Spyder est détecté.
- **Motivation** : conflits d'environnements de plugins Qt / noyau.
- **État** : implémenté ; test Windows réel à renouveler. **Sources** : `run.py`, `spyder_launch.py`, `GUIDE_STABILITE_SPYDER.md`.

## ADR-012 — Internationalisation externe et données scientifiques immuables

- **Décision** : sept catalogues XML à clés communes ; jamais de traduction automatique de sigles, noms de fichiers, TEI, ALTO ou JSON persistant.
- **Motivation** : UI locale sans altérer l'identité des données scientifiques.
- **État** : 653 clés remplies par langue (v0.8.5.5) ; révision native encore requise. **Sources** : `i18n.py`, `i18n/*.xml`, `docs/I18N_NATIVE_REVIEW_V0855.md`.

## ADR-013 — Navigation simple avant sophistication

- **Décision** : démarrer avec une image locale, un témoin et sans TEI, puis enrichir progressivement ; conserver des choix de configuration facultatifs.
- **Motivation** : usage pédagogique et absence de surcharge d'installation.
- **État** : principe produit implémenté globalement mais doit continuer à être évalué dans la GUI réelle. **Sources** : `core.new_project`, `resource_workflow.py`, `GUIDE_PERIMETRE.md` et décisions de projet.

## ADR-014 — Architecture Varians multi-fichiers : ne pas anticiper indûment

- **Contexte** : pour l'éditeur Varians, deux structures sont **en discussion** : plusieurs fragments XML composant une édition logique et plusieurs éditions autonomes dans un même projet ; scénarios XSLT personnalisables également étudiés.
- **Décision pour Synchro v0.8.5.6** : **aucune implémentation de ces scénarios n'est présumée**. `varians_project_export` copie actuellement une TEI pivot unique dans `xml/edition.xml` ; tout support futur doit avoir sa propre conception, matrice de compatibilité et migration documentée.
- **État** : besoin potentiel **non développé dans la présente version**.

## ADR-015 — Version 0.8.5.6 : documentation seulement

- **Décision** : passer `core.VERSION` à `0.8.5.6`, ajouter un dossier de passation autonome, une cartographie générée et des tests d'intégrité documentaire ; ne pas toucher aux algorithmes, catalogues ni format `.vsynch`.
- **Motivation** : transmettre le logiciel sans l'historique de conversation et sans augmenter le risque de régression.
- **État** : consigne de livraison de ce lot ; **voir tests** `TESTS_V0856.md`.

## ADR-016 — Projet Varians sans TEI : la TEI vide de Varians, le pivot préparé par Varians

- **Contexte** : l'export « Créer un projet Varians pré-renseigné… » exigeait une édition TEI associée au pivot, alors que Varians crée un projet sans TEI (« Commencer une nouvelle transcription ») et prépare ensuite les `<pb/>` et `<lb/>` du pivot dans la TEI vide.
- **Décision** : sans TEI associée au pivot, le projet reçoit la TEI vide de Varians, identique octet pour octet (`varians_project_export.blank_tei_edition`). La préparation des `<pb/>`/`<lb/>` reste à Varians (Fichier → « Paramètres du projet… ») : son code lit déjà les JSON d'alignement de Synchro et complète le `<facsimile>` ; le recopier dans Synchro obligerait à suivre ses évolutions.
- **État** : implémenté. **Tests** : `tests/test_varians_blank_edition.py` (vrai code de Varians), `tests/test_varians_export_gui_qt.py`, `tests/test_finalization_0851.py`.
