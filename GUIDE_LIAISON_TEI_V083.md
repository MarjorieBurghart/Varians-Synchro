# Varians-Synchro — V0.8.2 + V0.8.3 — Intégration TEI et rattachement physique

## Objectif

Associer une édition TEI à **un témoin identifié**, à partir de ses `<lb edRef="#SIGLE"/>`, puis rattacher ces lignes éditées aux lignes physiques des images ALTO/PAGE. Cette relation est **distincte** des alignements entre témoins (Mu↔F, etc.). Aucune TEI ni aucun XML ALTO/PAGE n'est modifié.

## Mode opératoire

1. Dans « Projet et témoins », ouvrir la fiche du témoin et importer la TEI. Son nom et le nombre de `<lb/>` du témoin peuvent être inspectés ; la TEI reste non liée.
2. Associer au préalable les images locales ou IIIF aux fichiers ALTO/PAGE du témoin.
3. Dans la synchronisation visuelle, **délimiter le périmètre** : marquer les lignes hors édition « Ignorées / hors périmètre ». Vérifier l'ordre des pages et des colonnes.
4. Dans **« Pages et ALTO/PAGE »**, cliquer **« Lier la TEI aux lignes ALTO/PAGE… »**.
5. Choisir le témoin et la TEI. Lire l'effectif de chaque côté et les éventuels diagnostics (notamment les lectures TEI indéterminées).
6. Si les effectifs concordent, examiner les paires proposées par **ordre de lecture continu**, y compris entre plusieurs folios. Confirmer la liaison, puis sauvegarder le `.vsynch`.

Il ne suffit pas d'importer le document TEI : il faut confirmer la liaison après contrôle des lignes physiques actives.

## Contrat TEI et apparat

- Seuls les `<lb/>` dont **`@edRef` contient exactement `#SIGLE`** sont recensés. Un `@edRef` manquant n'autorise aucune attribution implicite.
- Le contenu ordinaire est reconstitué de manière continue entre les `<lb/>` concernés, en conservant les textes inclus dans `<hi>`, `<seg>`, etc.
- Dans `<app>`, une seule `<lem>` ou `<rdg>` dont `@wit` inclut le sigle est retenue. S'il n'existe pas de lecture unique, l'ambiguïté **bloque** la liaison automatique. Il ne faut jamais concaténer des lectures concurrentes ni attribuer arbitrairement un `<lem>` non marqué.
- Dans `<choice>`, le texte sélectionné suit l'ordre `reg`, `corr`, `expan`, `orig`, `sic`, `abbr` : une seule branche est parcourue. Cette politique, destinée à la lecture éditée, est explicite et pourra être configurable dans une évolution ultérieure.
- Les `<note>`, `<fw>`, `<figure>` et `<facsimile>` ne sont pas intégrés à la ligne éditoriale. Les sauts de page `<pb>` apportent un repère documentaire sans limiter l'alignement physique.
- Les documents présentant plusieurs éléments `<text>` indépendants (par ex. certains `teiCorpus`) sont refusés pour ce rattachement global ; choisir une édition logique unique.

## Conventions et limites

Un nombre égal de `<lb/>` et de lignes ALTO/PAGE actives permet une **proposition ordinale**, pas une preuve philologique. Les omissions, segments déplacés ou discontinuités doivent être examinés avant validation. Une différence d'effectif nécessite de corriger d'abord le périmètre ou le document ; le programme n'invente pas de lignes ni de correspondances `n↔m` TEI/physique.

La liaison est enregistrée dans la ressource TEI, sous `tei_binding` (liste des clés TEI, identifiants physiques stables, empreintes et métadonnées de folio). Les `pair_sessions`, leur validation et les `base_keys` d'export vers Varians sont conservés à l'identique.

Si la TEI, la segmentation, le périmètre ou l'ordre de lecture changent, **l'état de la liaison devient « à revérifier »**. Elle n'est pas reconstruite implicitement ; une nouvelle confirmation est nécessaire. Pour l'instant, l'interface ne remplace pas encore « Texte HTR » par le texte TEI : l'affichage TEI et la recherche textuelle sont prévus en V0.8.4.

## Tests essentiels

- Une TEI à apparats où Mu et F portent des lectures différentes : aucun mélange.
- Des `<lb edRef="#F"/>` dans une édition de Mu : ils ne gonflent pas le nombre de lignes Mu.
- Un passage commençant au milieu d'un folio et s'achevant sur le folio suivant.
- Écart d'effectifs : pas d'édition automatique du projet.
- Modification d'une source TEI ou des lignes ignorées entre l'aperçu et l'enregistrement : refus d'une prévisualisation périmée.
- Réouverture du `.vsynch` : conservation des liaisons éditoriales et des sessions d'alignement existantes.

## Corrections ultérieures

Quand un nouveau périmètre ou un réordonnancement modifie la séquence physique tout en conservant la même TEI, la fenêtre peut proposer de **revalider** la liaison, toujours après contrôle et confirmation. Si le fichier TEI a changé, utiliser d'abord « Réanalyser le fichier TEI » : l'ancienne liaison passe en historique dans le projet et les nouvelles associations restent à confirmer. Les sessions d'alignement des manuscrits ne sont pas supprimées.

### Définir le périmètre avec un seul témoin

Depuis « Pages et ALTO/PAGE », le bouton **« Définir le périmètre physique du témoin… »** ouvre un visualiseur même en l'absence d'une session Mu–F. Les lignes peuvent être sélectionnées sur plusieurs folios. Les changements sont préparés dans une copie du projet : **« Annuler » n'enregistre rien**. La suppression éventuelle de liens déjà présents demande confirmation.
