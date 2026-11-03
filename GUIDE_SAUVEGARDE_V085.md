# Sauvegardes `.vsynch` — V0.8.5

## Fonctionnement

- Un premier enregistrement produit seulement `edition.vsynch`.
- Le suivant écrit le nouveau `edition.vsynch` et conserve le **précédent** sous `edition.vsynch.bak`.
- À chaque nouvelle sauvegarde, la `.bak` représente l'état **immédiatement antérieur** à celui du fichier principal.
- Le fichier principal est remplacé atomiquement, mais cela ne protège pas d'une erreur logique ayant déjà été sauvegardée. Pour les projets importants, conserver aussi des copies datées externes.

## Si un projet paraît vide ou illisible

1. **Ne pas utiliser Enregistrer** dans la fenêtre suspecte.
2. Fermer le logiciel sans enregistrer et copier `edition.vsynch` et `edition.vsynch.bak` dans un dossier de sécurité.
3. Examiner la copie `.bak` (JSON texte UTF-8) ou l'ouvrir dans Varians-Synchro par « Ouvrir », en choisissant « Tous les fichiers » si le sélecteur ne propose que `.vsynch`.
4. Pour restaurer, recopier la `.bak` vers **un nouveau fichier** `edition_restauree.vsynch`, puis ouvrir ce nouveau fichier.
5. Ne jamais effacer le fichier original avant de vérifier témoins, pages, TEI et groupes de correspondances.

## Portabilité

La `.bak` sauvegarde les références externes du projet, mais **ne copie pas les images, TEI, ALTO/PAGE ou les services IIIF**. Si ces sources ont changé de chemin, il faut les relocaliser après récupération.

La sauvegarde automatique ne répare pas les repères contradictoires et ne modifie jamais une lecture TEI ambiguë.
