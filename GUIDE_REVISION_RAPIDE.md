# Guide V0.7.2 — Vérifier rapidement les alignements

1. Faire une copie de sauvegarde de votre `.vsynch` et ouvrir la V0.7.2.
2. Calculer et enregistrer les propositions **Synchroniser entre repères (texte)**.
3. La barre **Vérification** affiche par défaut les **groupes à vérifier**, triés selon l’ordre de lecture continu, folios et colonnes compris.
4. Sélectionner un groupe pour afficher ses lignes dans les deux visualiseurs. **F8 / Suivant** passe au suivant, **Maj+F8 / Précédent** au précédent.
5. Contrôler le passage et choisir **Valider et suivant** (ou **Alt+V**) : un seul groupe est validé et le suivant apparaît.
6. Pour plusieurs groupes déjà examinés, les sélectionner avec Ctrl ou Maj dans la liste puis utiliser **Valider la sélection…**. Une confirmation explicite est exigée et les empreintes ALTO/PAGE sont vérifiées de façon atomique.
7. Pour corriger une association, utiliser **Associer les lignes**, **Dissocier** ou déclarer une **Absence confirmée** comme auparavant. Une correction humaine n’est jamais révisée silencieusement.
8. Pour recalculer un passage local, passer au filtre **Validés**, sélectionner le repère de début validé, puis cliquer sur **Recalcul local…**. Seules les propositions situées avant le repère validé suivant sont présentées ; le reste du projet est conservé.
9. Enregistrer le projet et exporter les JSON destinés à Varians.

**Principes de sécurité :** il n’y a pas de validation automatique de masse. Une ligne hors périmètre reste ignorée. Une absence confirmée n’est jamais transformée en correspondance. La validation échoue complètement si une source XML ne correspond plus à l’empreinte enregistrée. Les corrections manuelles et groupes validés restent protégés des recalculs. Les boutons de navigation ne modifient pas les données.

**À noter :** les six tests graphiques Qt préexistants ne sont pas exécutables ici sans PySide6. L’affichage et les raccourcis devront être vérifiés dans Spyder/Windows. Lancement isolé V0.7.1.1 conservé.
