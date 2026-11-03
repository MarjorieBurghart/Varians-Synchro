# Varians-Synchro V0.7.2.2 — Réordonnancement visuel des pages

Cette livraison reprend la **V0.7.2.1** et conserve sans changement le moteur
V0.7.1, les vérifications rapides V0.7.2 et la confirmation de sauvegarde.

## Mode d'emploi

1. Ouvrir le projet et choisir **2 · Pages et ALTO/PAGE**.
2. Cliquer sur **« Gérer les pages, leur ordre et les associations ALTO/PAGE… »**.
3. Vérifier les miniatures et les libellés. Glisser les pages dans l'ordre souhaité,
   utiliser **Monter / Descendre** pour une page, ou **Inverser l’ordre** pour une
   série importée à l'envers.
4. Fermer la fenêtre puis enregistrer le `.vsynch`.

Les miniatures des **images locales** sont décodées en basse résolution par Qt,
uniquement quand les lignes deviennent visibles dans la liste. Les **Canvas IIIF**
avec un service IIIF Image obtiennent des aperçus de 180 pixels, à la demande,
sans télécharger 469 images à l'ouverture d'un grand Manifest. Pour les Canvas
qui ne proposent qu'une URL d'image directe, ou pour les formats non décodables
par Qt, le nom de la page reste visible mais l'aperçu peut être absent.

## Garantie sur les associations

Les opérations de réordonnancement écrivent uniquement `reading_order` dans
chaque entrée de `witness.pages`. Elles n'ouvrent, ne renommeront et n'écrivent
jamais les originaux image ou ALTO/PAGE et conservent sans modification :

- `page.id`, `image_path`, `image_source_id`, `canvas`, `alto_binding` ;
- les identifiants physiques des lignes et leurs coordonnées ;
- `pair_sessions` et les validations existantes ;
- les règles d'exclusion de lignes et les références exportables pour Varians.

Le `ProjectChangeTracker` de la V0.7.2.1 détecte le changement d'ordre : une
fermeture sans sauvegarde affiche donc l'avertissement habituel.

## Contrôle qualité

- 201 tests réussis, 7 tests graphiques PySide6 ignorés dans cet environnement.
- Tests nouveaux : ordre inversé, déplacement par identifiant stable,
  rejet atomique d'ordres incomplets, associations PAGE préservées,
  enregistrement/relecture `.vsynch`, indicateur non enregistré, libellés FR/EN.
- Interfaces Qt et miniatures distantes à vérifier sur un poste disposant de PySide6.

## Ajout de pages après réordonnancement

Quand l'utilisateur a déjà enregistré un ordre manuel puis importe d'autres
images, les nouvelles pages sont ajoutées en fin de liste. Le réordonnancement
précédent n'est pas perdu et peut être complété par glisser-déposer.
