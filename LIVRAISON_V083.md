# Livraison — Varians-Synchro V0.8.3

Regroupe **V0.8.2 (lecture TEI par témoin)** et **V0.8.3 (rattachement TEI ↔ ALTO/PAGE)** sur la base V0.8.1.2.

- Les fichiers **ALTO/PAGE/TEI originaux ne sont jamais modifiés**.
- Les liens TEI ↔ lignes physiques sont enregistrés dans les ressources TEI du `.vsynch`, séparément des `pair_sessions` entre manuscrits.
- L'étape « Pages et ALTO/PAGE » dispose maintenant des commandes **« Définir le périmètre physique du témoin… »** et **« Lier la TEI aux lignes ALTO/PAGE… »**.
- Extraction conservatrice de la TEI par `@edRef` et `@wit` ; les apparats impossibles à attribuer de façon unique bloquent une liaison en masse.
- Prévisualisation fondée sur l'égalité des effectifs et l'ordre de lecture, confirmation explicite, vérification d'empreintes et signalement des ressources périmées.
- Réanalyse explicite et archivage de l'ancienne liaison si le fichier TEI a changé.
- Moteur V0.7.4 **inchangé** ; les fichiers `textual_progress.py`, `physical_alignment.py`, `reading_stream.py` et `varians_export.py` correspondent aux versions de V0.8.1.2.
- Le texte TEI ne remplace **pas encore** la HTR dans le visualiseur : fonction prévue pour V0.8.4, avec recherche textuelle.

## Tests

`python -m pytest -q` : **268 réussis, 9 ignorés** (PySide6 absent de l'environnement de recette). Les nouveaux écrans devront être essayés sous Windows/Spyder.

Voir `GUIDE_LIAISON_TEI_V083.md`, `CHANGELOG_V083.md` et `TESTS_V083.md`.
