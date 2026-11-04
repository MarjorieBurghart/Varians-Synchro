# Red team : intégrité, fichiers reçus, moteurs, interface

Version examinée : commit `0eefc7b` (après la fusion des PR #19 à #24), avant le
passage de version. Corrections : branche `claude/red-team`.

## Objet

Quatre questions, avant de publier une nouvelle version :

- **Intégrité des données** : ce que Varians-Synchro enregistre et exporte
  vers Varians est-il exact (lignes du pivot, clés, périmètre, chemins,
  droits des fichiers) ?
- **Fichiers et données reçus** : que peut faire un `.vsynch`, une TEI, un
  fichier ALTO/PAGE, une image ou un serveur IIIF reçus d'un tiers ?
- **Moteurs** : justesse et temps de calcul sur de grands manuscrits ou des
  fichiers inhabituels.
- **Interface et cohérence** : clavier, petits écrans, traductions, fenêtres
  qui se contredisent ou perdent du travail.

## Méthode

1. Quatre agents ont cherché en parallèle, chacun sur un terrain :
   A intégrité des données ; B fichiers et données reçus ; C moteurs ;
   D interface Qt et cohérence. Chaque piste est venue avec une preuve
   (script ou projet d'essai) ; aucun n'a modifié le dépôt.
2. Chaque piste a été vérifiée à la main ; les points vérifiés sains sont
   repris plus bas.
3. Huit choix de comportement ont été posés à l'utilisatrice (voir
   « Décisions ») ; un neuvième, sans question, lui a été annoncé.
4. Chaque faiblesse a d'abord été reproduite par un test, vu en échec ; puis
   corrigée, un commit par étape, la suite complète verte à chaque fois
   (684 tests à la fin, dont l'interface Qt), puis la suite entière répétée
   pour vérifier la sortie du processus (voir « Trouvé en vérifiant »).

## Décisions de l'utilisatrice

| Question | Réponse |
|---|---|
| A1 Lignes ignorées après une nouvelle segmentation | Reporter la marque sur la ligne retrouvée à l'identique (même identifiant ALTO, même texte), sinon la retirer en le disant dans la confirmation. |
| A2 Export avec une liaison TEI du pivot périmée | Refuser, avec le motif et l'étape où refaire la liaison. |
| A4 Sigles des témoins | Comme Varians : sigles libres ; les exports en tirent l'identifiant XML par la règle de Varians ; deux sigles de même identifiant refusés dès la création. |
| B3 Projet reçu qui désigne des fichiers hors de son dossier ou sur un partage réseau | Demander à l'ouverture (« Non » par défaut) ; refusés, ces fichiers sont introuvables, et leurs chemins sont gardés à l'enregistrement. |
| D3 Fenêtre de synchronisation trop large | Commandes des panneaux et barre de révision sur deux rangées ; largeur minimale ≤ 1 280 px dans les sept langues, vérifiée par un test. |
| D2, D6 Touche Entrée et confirmations | Entrée n'active plus de bouton par défaut ; dans une liste, elle fait comme le double-clic ; toutes les questions ont « Non » par défaut. |
| D12 Échap ou la croix sur un brouillon | Demander avant d'abandonner un brouillon modifié (fiche du témoin, périmètre) ; sans changement, fermer directement. |
| C4, C5 Fichiers PAGE à structure imbriquée | Corriger pour les nouveaux imports ; l'audit signale les fichiers déjà importés que cette version lit autrement, sans les modifier. |
| B5 Formats d'image (annoncé sans question) | Seuls JPEG, PNG, TIFF, WebP et JPEG 2000 sont décodés comme images de page ; SVG et PDF ne le sont plus. |

## Faiblesses trouvées et corrigées

Gravité : ce que permet la faiblesse, à partir d'un fichier reçu ou d'un
usage ordinaire.

### Intégrité des données (A)

| Id | Gravité | Constat | Correction | Tests | Commit |
|---|---|---|---|---|---|
| A1 | haute | Une ligne ignorée n'est connue que par sa page et son rang. Quand la page recevait un autre fichier ALTO/PAGE, ou que son fichier était retiré, la marque passait sans avertissement à la ligne qui prenait ce rang : un titre courant revenait dans le pivot exporté, une vraie ligne en sortait. | `imaging.bind_alto` reporte la marque sur la ligne retrouvée à l'identique et retire les autres (`line_scope.carry_ignored_lines`) ; retirer un fichier retire les marques de ses pages ; les confirmations disent combien de marques seront perdues. | `test_ignored_lines_rebind.py`, `test_resource_removal.py` | 6bee001 |
| A2 | moyenne | « Créer un projet Varians pré-renseigné » acceptait une liaison TEI du pivot périmée : les `<lb/>` de la TEI copiée se trouvaient en face d'autres lignes, sans que Varians puisse le voir. | Export refusé, avec le motif (`error.project_export.tei_binding_stale`). | `test_project_export_tei_stale.py` | 52eacd5 |
| A3 | moyenne | Déplacer une région effaçait sans prévenir l'ordre des lignes corrigé de la page. | L'ordre des lignes est retrié selon le nouvel ordre des régions. | `test_reading_order_followed.py` | 45f7622 |
| A4 | moyenne | Un sigle comme « BnF lat. 123 » était accepté à la création puis refusé par les deux exports, sans moyen de le corriger (le sigle entre dans l'identifiant de chaque ligne). | `witness_ids.py` reprend la règle de Varians ; les exports nomment témoins et fichiers par l'identifiant XML ; deux sigles de même fichier et les noms réservés par Windows sont refusés dès la création. | `test_witness_sigla.py`, `test_release_074.py` | 81aca73 |
| A5 | moyenne à basse | Retirer un ancien ALTO, dont la continuité des identifiants PERO gardait trois groupes à l'export, annonçait « 0 groupe » et l'export les perdait. | `removal_impact` compte aussi ces groupes (`varians_export.links_kept_by_uuid_continuity`). | `test_resource_removal.py` | 6bee001 |
| A6 | basse | L'association manuelle acceptait la même page ALTO/PAGE pour deux images : ses lignes comptaient deux fois dans le pivot exporté. | Refus, comme l'association par lots ; l'audit signale les projets anciens concernés. | `test_engine_details.py` | ad9fb77 |
| A7 | basse | Un nom de fichier contenant « \ » (Linux, macOS) était relu comme un séparateur ; ouvrir puis enregistrer un projet dont le dossier contient un lien symbolique rendait absolu un chemin relatif. | `os.path.normpath` à l'ouverture ; chemin absolu gardé pour un nom contenant « \ ». | `test_received_project_paths.py` | a449f80 |
| A8 | basse | Le premier `.vsynch` était créé en 0600 et les dossiers d'export en 0700 : une équipe sur un partage ne pouvait pas les lire. | Droits selon le masque de l'utilisateur (`core.default_mode`). | `test_received_project_paths.py` | a449f80 |

### Fichiers et données reçus (B)

| Id | Gravité | Constat | Correction | Tests | Commit |
|---|---|---|---|---|---|
| B1 | moyenne | Un sigle, un texte HTR ou TEI, un nom de projet ou la réponse d'un serveur IIIF étaient affichés par Qt comme du HTML dès qu'ils ressemblaient à une balise : faux messages, fichiers locaux chargés (réseau sous Windows). | Texte brut pour les étiquettes, les boîtes de message (dont l'erreur imprévue) et les infobulles qui citent une donnée ; sigle échappé dans l'en-tête du visualiseur. | `test_plain_text_qt.py`, `test_error_report_qt.py` | 45296e3, 7608e2e |
| B2 | moyenne | Les miniatures IIIF n'avaient ni contrôle du schéma (`file://` lisait le disque) ni limite de taille (600 Mo en mémoire pour une vignette). | http/https seulement ; réponse abandonnée au-delà de 2 Mo. | `test_page_images_qt.py` | b7e8e98 |
| B3 | moyenne | À l'ouverture, un `.vsynch` reçu faisait lire des fichiers hors de son dossier (« ../../Documents/… ») ou sur un partage réseau ; l'export copiait la TEI désignée. | Question à l'ouverture (`core.suspicious_paths`) ; refusés, ces fichiers sont introuvables (`load_project(refused=…)`), leurs chemins gardés à l'enregistrement. | `test_received_project_paths.py` | a449f80 |
| B4 | moyenne | Un serveur lent figeait la fiche du témoin (Manifest chargé dans le fil de l'interface) ; le délai ne portait que sur chaque lecture, et l'annulation des copies HD restait sans effet. | Manifest chargé dans un fil à part, attente annulable ; échéance totale par téléchargement (120 s ; 600 s pour une copie HD). | `test_network_limits.py`, `test_manifest_retry_qt.py` | f84a140, b7e8e98 |
| B5 | basse | Une « image » de page qui était un SVG (ou un PDF) était décodée ; le SVG pouvait charger des fichiers locaux ou réseau. | Formats décodés limités (voir « Décisions »). | `test_page_images_qt.py` | b7e8e98 |
| B6 | basse | Une TEI imbriquée sur 1 200 niveaux levait une `RecursionError` : la fenêtre principale ne pouvait plus se rafraîchir. | Message (`error.tei_binding.too_deep`). | `test_received_project_paths.py` | a449f80 |
| B7 | basse | Le ZIP « Exporter pour HTR » nommait ses images d'après le sigle : un sigle « ../../… » donnait des chemins hors du dossier à la décompression. | Noms tirés de l'identifiant XML (`witness_ids`). | `test_witness_sigla.py` | 81aca73 |
| B8 | basse | Le contrôle http/https ne portait que sur l'adresse de départ : une redirection vers `ftp://` était suivie. | Ouvreur qui refuse toute redirection hors http/https. | `test_network_limits.py` | f84a140 |

### Moteurs (C)

| Id | Gravité | Constat | Correction | Tests | Commit |
|---|---|---|---|---|---|
| C1 | haute | Enregistrer des propositions relisait toutes les lignes des deux témoins pour chaque groupe : 3 min 30 s pour 3 000 lignes, fenêtre figée. | Contexte calculé une fois par lot ; 0,5 s pour 3 000 lignes, mêmes résultats. | `test_engine_scaling.py` | 65b43c6 |
| C2 | moyenne | La proposition HTR–HTR ignorait l'ordre de lecture corrigé : « Ancrages non monotones » et aucune proposition, ou des propositions fausses, pour des feuillets reliés dans le désordre. | Les deux flux suivent `reading_stream`. | `test_reading_order_followed.py` | 45f7622 |
| C3 | moyenne | Après la correction d'un groupe automatique, « Recalculer jusqu'au prochain ancrage » ne proposait plus rien dans l'intervalle. | Chaque proposition garde les ancrages validés qui l'entourent (`evidence.anchor_start`, `anchor_end`). | `test_engine_details.py` | ad9fb77 |
| C4 | moyenne | PAGE : un ReadingOrder à groupes imbriqués (OCR-D, Aletheia) était lu dans le désordre, sans avertissement. | Chaque groupe trié par son propre index ; l'audit signale les fichiers déjà importés que cette version lit autrement. | `test_page_nested.py` | 94fa595 |
| C5 | basse | PAGE : une TextRegion dans une autre comptait deux fois les lignes de la région intérieure. | Une région ne prend que ses propres lignes. | `test_page_nested.py` | 94fa595 |
| C6 | basse | Le second passage résiduel proposait d'étendre un groupe périmé, et l'enregistrement, tout ou rien, refusait alors toute la sélection. | Les groupes périmés ne servent plus de voisins. | `test_engine_details.py` | ad9fb77 |
| C7 | basse | La réimportation des résultats HTR n'était pas atomique : un XML tronqué laissait le témoin à moitié modifié. | Tout ou rien. | `test_engine_details.py` | ad9fb77 |
| C8 | basse | Interpolation géométrique (menu de compatibilité) lente sur une longue colonne : 9,4 s pour 222 lignes. | Textes normalisés une fois, comparaisons écartées par leurs bornes rapides : 7,3 s, même résultat (voir « Limites »). | `test_engine_scaling.py` | 65b43c6 |

### Interface et cohérence (D)

| Id | Gravité | Constat | Correction | Tests | Commit |
|---|---|---|---|---|---|
| D1 | critique | Fermer la fenêtre des pages pendant un téléchargement annulé (copies HD, export pour HTR) détruisait le fil en cours : arrêt brutal, travail non enregistré perdu. | `ui_widgets.start_detached` : fil sans parent, annulé avec sa fenêtre, libéré à sa fin. | `test_pages_threads_qt.py` | c64eb60 |
| D2 | haute | Entrée déclenchait le premier bouton : une page remontait d'un rang (pivot compris), un groupe manuel validé était créé. | Voir « Décisions ». | `test_keyboard_qt.py` | 45ed84f |
| D3 | haute | La fenêtre de synchronisation demandait 1 600 à 1 700 px : sur un portable, le bord droit sortait de l'écran. | Voir « Décisions » ; fenêtres de taille fixe bornées à l'écran (`fit_to_screen`). | `test_small_screen_qt.py` | a7f3b94 |
| D4 | moyenne à haute | Les associations faites dans la fiche d'un nouveau témoin (« Associer automatiquement… ») étaient perdues dès qu'on touchait à la description, au pivot ou aux ressources. | Elles sont refaites quand le brouillon est reconstruit. | `test_witness_card_qt.py` | 6b946eb |
| D5 | moyenne | « Ajouter un témoin… » avec un sigle déjà pris complétait en silence le témoin existant (le pivot compris). | Refus. | `test_witness_sigla.py` | 81aca73 |
| D6 | moyenne | Trois confirmations destructives répondaient « Oui » à Entrée. | « Non » par défaut. | `test_keyboard_qt.py` | 45ed84f |
| D7 | moyenne | Les boutons standard de Qt (« Yes », « No », « OK », « Cancel ») restaient en anglais. | Traductions de Qt livrées par PySide6, chargées pour la langue choisie. | `test_remaining_translations.py` | a531b51 |
| D8 | basse à moyenne | Diagnostics de la liaison TEI et avertissements de l'association par lots écrits en français dans le code ; « [ligne modifiée] » non traduit. | Messages à clé, ×7. | `test_remaining_translations.py` | a531b51 |
| D9 | basse à moyenne | F1 n'ouvrait l'aide que dans deux fenêtres. | F1 dans toute fenêtre. | `test_keyboard_qt.py` | 45ed84f |
| D10 | basse | La fiche d'un témoin ne s'ouvrait qu'à la souris ; ni Ctrl+S, ni Ctrl+O, ni Ctrl+N. | Entrée, Espace ; raccourcis standard. | `test_keyboard_qt.py` | 45ed84f |
| D11 | basse | Après « Ordre de lecture et intervalles… », Maj+clic suivait l'ancien ordre dans la synchronisation. | Les panneaux relisent l'ordre. | `test_reading_order_followed.py` | 45f7622 |
| D12 | basse | Échap ou la croix jetaient sans rien demander le brouillon d'une fiche ou du périmètre. | Voir « Décisions ». | `test_keyboard_qt.py` | 45ed84f |
| D13 | basse | « Réessayer » après « − » levait une `KeyError` ; la confirmation des associations « par ordre » comptait les lignes changées à la main ; décocher la case pivot dans la fiche du pivot était sans effet ; ouvrir puis fermer une paire créait une session vide et marquait le projet modifié. | Corrigés un à un ; la case pivot du pivot est grisée, avec une infobulle (×7). | `test_witness_card_qt.py` | 6b946eb |

### Trouvé en vérifiant

| Id | Gravité | Constat | Correction | Tests | Commit |
|---|---|---|---|---|---|
| V1 | moyenne (CI) | La suite entière réussissait, puis le processus s'arrêtait une fois sur huit environ sur une erreur de segmentation, à l'arrêt de Python (`QObject::~QObject` dans `PySide::destroyQCoreApplication`, pile obtenue sous gdb) : PySide détruisait alors les fenêtres que les tests n'avaient pas libérées (43 à la fin de la suite), dont des fenêtres encore reliées par `start_detached` à une fonction Python. Non reproduit sur `main` en 12 passages. | `start_detached` défait ce lien dès que le fil a fini ; les tests concernés libèrent leurs fenêtres ; `tests/conftest.py` libère celles qui resteraient avant l'arrêt de Python (plus aucune laissée à PySide). | `test_detached_threads_qt.py` ; suite répétée | voir la PR |

## Vérifié sain

- **XML** : ni entités externes ni DTD résolues ou téléchargées ; « billion
  laughs » et explosion quadratique bloqués par expat (2.6.1 ici).
- **Images** : un PNG de 40 000 × 40 000 est refusé (limite d'allocation de
  Qt) ; tailles de téléchargement plafonnées (Manifest 20 Mo, image 80 Mo,
  copie HD 160 Mo) ; redirection vers `file:` refusée.
- **Copies HD** : noms nettoyés, dossier vide exigé, publication atomique ; le
  reçu `images.json` refuse `../`, `\`, les chemins absolus et les liens
  symboliques. `import_htr_results` n'utilise que le nom de base.
- **Enregistrement** : fichier temporaire avec `fsync`, `.bak` des octets
  précédents, `os.replace`, destination en lien symbolique refusée, droits
  gardés quand on écrase un fichier ; aller-retour enregistrer/rouvrir
  identique ; chemins Windows (casse, UNC, autre lecteur) traités juste.
- **Exports** : dossier préparé à part, relu, publié par `os.replace`,
  destination vide exigée ; XML produit par ElementTree, donc échappé ; clés
  du pivot justes avec un ordre corrigé, des groupes n↔m, une session dans
  l'autre sens, une absence confirmée ; lignes ignorées exclues sans
  renumérotation.
- **Liens** : empreintes et `link_is_stale` détectent un décalage de rang ou
  un changement de texte, d'identifiant ou de cadre ;
  `replace_revisable_pair_proposals` (3 000 sessions au hasard) ne touche
  jamais un groupe validé ou manuel, ni une absence, et aucune ligne
  n'appartient à deux groupes ; les opérations sur les groupes, le
  périmètre, la liaison TEI et l'association par lots valident avant de
  modifier (tout ou rien).
- **Moteurs** : ALTO inhabituels (coordonnées absentes, nulles, négatives ou
  décimales, identifiants répétés, lignes sans texte, page vide) sans
  exception dans neuf moteurs ; pas de division par zéro ; progression
  textuelle (3 000 lignes) en 0,34 s, avec 1 000 ancrages en 1,5 s ;
  HTR–HTR en 1,8 s.
- **Interface** : toutes les phrases des fenêtres sont au catalogue ;
  « Annuler » ou « Fermer » sans action ne modifie pas le projet ; le
  changement de langue garde le projet et son état « modifié » ; les
  fenêtres sont libérées après fermeture ; le visualiseur reçoit ses images
  dans le fil de l'interface, et un panneau détruit avant la réponse ne plante
  pas.

## Limites connues

- **Lignes ignorées anciennes.** Rien ne garde la ligne d'origine d'une
  marque : un décalage survenu avant cette version (réassociation d'une page)
  ne peut pas être détecté par l'audit. Seules les nouvelles réassociations
  reportent ou retirent la marque.
- **Interpolation géométrique** (menu de compatibilité) : 7,3 s pour une
  colonne de 222 lignes au lieu de 9,4 s ; la comparaison des textes elle-même
  reste l'essentiel du coût.
- **Calculs dans le fil de l'interface.** Les propositions automatiques sont
  calculées sans fil à part ; l'enregistrement est désormais linéaire, mais un
  très grand manuscrit reste lent à calculer.
- **Windows non essayé ici.** Les accès réseau (SMB) que provoquaient les
  pistes B1, B2, B3 et B5 ont été montrés sous Linux (strace) ; les
  corrections les suppriment tous, sans essai sous Windows.

## Pistes non poursuivies

Plausibles, non prouvées, ou hors du sujet de cette red team :

- `pair_progress` compte comme couvertes les lignes des groupes périmés
  (l'export les exclut) : définition à trancher.
- La proposition HTR–HTR prend aussi les groupes périmés comme ancrages
  protégés : effet probable, des propositions manquées, non montré.
- Un lien sans empreintes serait jugé sain mais ne pourrait jamais être
  validé ; aucun chemin actuel ne crée un tel lien.
- Témoin mixte (IIIF et images locales) : les images locales suivent l'ordre
  d'import, non celui des folios ; pages sans folio placées après les autres.
- Fichiers PAGE 2010 (`<Coords><Point/>`) : leurs lignes sont seulement
  comptées comme « non segmentées ».
- Deux Manifests dont les Canvas n'ont pas d'`id` donnent des identifiants
  `canvas-1` en collision.
- `page_line_polygons` ne vérifie pas qu'un chemin désigne un fichier
  ordinaire (un `/dev/stdin` pourrait bloquer).
- Projets IIIF : l'export écrit des `<ocrLink>` vers les XML sur disque sans
  vérifier leur empreinte.
- Pas de `fsync` du dossier après `os.replace` ; `Path.resolve()` à
  l'enregistrement pourrait attendre un lecteur réseau injoignable.
- Changement de langue : la nouvelle fenêtre revient à l'étape 1 et l'aide
  ouverte se ferme (aucune donnée perdue).
- L'aperçu non modal d'une page garde l'ancienne segmentation après
  « Associer ALTO/PAGE » (affichage seulement).

## Où regarder dans le code

- `ui_widgets.py` : texte brut (`QLabel`, `message_box`, `plain_tip`),
  questions « Non » par défaut, `QDialog` (Entrée, F1, brouillon),
  `start_detached`, `decode_page_image`, `fit_to_screen`,
  `install_qt_translation`.
- `core.py` : `suspicious_paths`, `load_project(refused=…)`,
  `_with_relative_paths`, `default_mode`.
- `witness_ids.py` : identifiant XML et nom de fichier tirés du sigle.
- `imaging.py` : `bind_alto` (report des marques), ouvreur http/https,
  `_http_bytes` (taille, échéance), réimportation HTR tout ou rien.
- `line_scope.py` : `carry_ignored_lines` ; `resource_removal.py` : impact et
  retrait des marques.
- `physical_alignment.py` : `_link_context`, `page_links_impact`,
  `suggest_htr_pair_alignment`.
- `page_xml.py` : groupes et régions imbriqués ; `validation.py` :
  `xml_source_read_otherwise`, `xml_page_bound_twice`.
- `textual_progress.py`, `rapid_review.py` : `anchor_start`, `anchor_end`.
- `varians_project_export.py` : refus de la liaison TEI périmée ;
  `varians_export.py` : `witness_file_names`,
  `links_kept_by_uuid_continuity`.
- `ui_resources.py` : brouillon de la fiche du témoin (associations refaites,
  Manifest en fond, « Réessayer ») ; `ui_main_window.py` : chemins refusés,
  raccourcis, paire vide non gardée.
