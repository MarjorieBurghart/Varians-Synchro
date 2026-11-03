# Varians-Synchro V0.6.11 — Lignes hors périmètre

## Pourquoi « Ignorée » est une catégorie distincte

Les lignes figurant dans les images et ALTO d'un témoin peuvent appartenir à une autre œuvre. Elles ne doivent alors ni être rapprochées d'un autre témoin, ni entrer dans le dénominateur de progression. Cela ne signifie **ni lacune**, ni absence confirmée, ni erreur de l'ALTO. Une ligne appartient au périmètre du texte étudié, ou en est exclue, **au niveau du témoin pour tout le projet**, non au niveau d'une seule paire de témoins.

## Manipulations dans l'interface visuelle

1. Ouvrir une session sous **3 · Synchronisation**.
2. Cliquer sur une ou plusieurs lignes ALTO d'un témoin. Ctrl et Maj permettent de constituer des sélections multiples ; on peut également agir sur les deux témoins en une seule opération.
3. Choisir **Périmètre ▾ → Ignorer les lignes sélectionnées**.
4. Les rectangles deviennent **gris pointillé**. La progression indique séparément le nombre de lignes ignorées ; elles ne seront ni proposées par l'alignement HTR–HTR, ni utilisées par l'interpolation géométrique.
5. Pour annuler cette exclusion, sélectionner les lignes grises et utiliser **Périmètre ▾ → Réintégrer les lignes sélectionnées**.
6. **Enregistrer** le projet `.vsynch` dans la fenêtre principale.

Une ligne ignorée reste visible avec le filtre **Toutes les lignes**, et peut être sélectionnée (orange) pour être réintégrée. Les filtres **Non synchronisées** et **Automatiques à vérifier** la masquent, sans jamais cacher l'image du manuscrit. Le panneau texte facultatif la précède de la mention `[ignorée]` / `[ignored]`.

**Attention :** la sélection Maj travaille avec l'ordre des lignes ALTO de la page. Si l'ALTO entrelace mal deux colonnes, vérifier les cadres orange avant de confirmer une exclusion groupée. Le logiciel ne présume pas qu'un rectangle situé plus haut est forcément antérieur dans l'ordre de lecture.

## Lorsqu'une ligne est déjà associée

Le logiciel indique combien de groupes d'alignement seraient concernés et demande confirmation **avant** de supprimer leur référence à la ligne exclue. Les autres lignes des groupes 1↔n et n↔m restent associées si les deux côtés demeurent non vides. Si un groupe ne peut plus représenter de correspondance, il est supprimé (sans créer d'« absence confirmée » artificielle). Les groupes de **toutes les paires de témoins** dans lesquelles apparaît la ligne sont concernés. Si l'opération est annulée, aucun lien ni marquage n'est modifié.

Les **anciennes sessions TEI** reposent sur un modèle distinct. Si l'ALTO choisi est encore référencé par une telle session, le logiciel refuse l'exclusion pour préserver le travail éditorial : dissocier d'abord la ligne dans l'outil TEI historique. Cette restriction sera levée lorsque la migration des correspondances TEI sera pleinement intégrée.

## Code couleur

| Apparence | Statut |
|---|---|
| Violet soutenu (trait plein) | Non synchronisée, mais dans le périmètre |
| Vert (plein / pointillé) | Association manuelle validée / à vérifier |
| Bleu (plein / pointillé) | Proposition automatique validée / à vérifier |
| Gris pointillé | Ignorée, hors périmètre |
| Orange | Sélection de travail |
| Rose | Correspondance consultée dans l'autre manuscrit |
| Rouge pointillé | Absence textuelle confirmée |

Orange et rose ont toujours priorité d'affichage lors de la sélection ou de la consultation.

## Stockage et compatibilité

Le fichier `.vsynch` conserve une liste **`ignored_line_ids`** propre à chaque témoin. Elle contient les identifiants persistants des lignes ALTO, indépendamment des autres témoins et des sessions. Les versions antérieures, dans lesquelles cette liste n'existe pas, sont ouvertes sans migration destructive. Les fichiers ALTO XML, les images locales et les Manifests IIIF ne sont jamais modifiés.

Les catalogues `i18n/fr.xml` et `i18n/en.xml` contiennent les libellés du nouveau parcours. Ce correctif reste Python/PySide6 et multiplateforme : Windows, macOS et Linux selon la disponibilité de Python et Qt.
