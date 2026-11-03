# Varians-Synchro V0.7.1.1 — stabilité sous Spyder

## Ce qui change

Sous **Spyder/IPython**, `run.py` n'initialise plus PySide6 dans le noyau de Spyder. Il lance un **nouveau processus** qui utilise exactement `sys.executable` (le Python du noyau), puis rend immédiatement la main à Spyder. Cette séparation évite les conflits de runtime Qt/PyQt/PySide dans le noyau.

Depuis un terminal, `python run.py` démarre normalement l'interface dans le processus courant. Les données et les formats des projets `.vsynch` ne sont pas modifiés.

## Procédure

1. Décompresser la V0.7.1.1 dans un nouveau dossier, ouvrir **son** `run.py` dans Spyder et exécuter F5.
2. Observer dans la console Spyder le PID et le chemin du **journal de démarrage**.
3. Si une fenêtre ne s'ouvre pas, consulter le journal dans `~/.varians_synchro/logs/` (sur Windows `C:\Users\<utilisateur>\.varians_synchro\logs`).
4. Tester plusieurs démarrages *avec fermeture normale de la fenêtre entre deux essais*, et essayer aussi `start_isolated.py` si Spyder ne reconnaît pas son noyau.

Le lancement indépendant signifie qu'un redémarrage du noyau Spyder ne ferme plus la fenêtre Varians-Synchro. Fermer la fenêtre avant de relancer, ou vérifier le processus dans le Gestionnaire des tâches.

## Identification du problème

- Si le plantage disparaît : il était probablement lié au partage du processus Qt avec Spyder.
- Si le processus indépendant plante encore : transmettre le journal `demarrage_*.log`, la sortie de `diagnostic_spyder.py`, la version PySide6 et l'OS. Il peut s'agir d'un conflit de DLL, de plugins de plateforme, de versions Qt ou de pilotes.
- Une erreur fatale native peut arrêter Python sans traceback Python ; le mode `faulthandler` améliore le diagnostic sans garantir une explication à tous les crashs.

Ne pas mélanger des installations PyQt/PySide ni modifier les installations de Qt avant d'avoir identifié la cause.

## Tests

Les tests unitaires vérifient la détection du noyau, l'absence de boucle de relancement, l'héritage de l'interpréteur Python, le nettoyage des chemins de plugins et la création du journal. Ils ne remplacent pas les essais Windows/Spyder réels.
