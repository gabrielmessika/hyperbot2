# HyperBot2 0.2.0 — acceptation serveur

**Exécutable installé et vérifié sur le serveur existant**, indépendamment des
anciens bots. Release : `b44a0baa421ac7f2`, image Docker du même identifiant,
installation `/opt/hyperbot2/current`. Le service a été arrêté proprement après
validation ; aucun conteneur ne tourne au contrôle final.

## Comportement livré

- CLI installée : `run`, `health`, `status`, `prepare`, `replay`, `shadow`,
  `catalog`, `screen`, `witness` et `--version`.
- Service public borné, verrou d’instance, états atomiques et heartbeat.
- Raw persisté avant interprétation, conversion automatique en fenêtres,
  rotation entre les marchés et passage aux deux moteurs de simulation.
- Jointure offline de références de settlement datées et checksumées ; les
  observations futures ne deviennent pas disponibles avant leur réception.
- Arrêt SIGTERM/SIGINT avec finalisation, budget court sur inputs bloqués,
  détection d’interruption précédente, erreur disque sans collector suspendu.
- Déploiement par artefacts vérifiés, release immuable et pointeur `current`.

## Vérifications

| Vérification | Résultat |
|---|---|
| Tests locaux | **149 passés** |
| Ruff / mypy strict | Succès, 43 modules source vérifiés par mypy |
| Build et installation | Wheel 0.2.0, dépendance verrouillée avec hashes, version exécutée sur serveur |
| Santé pendant le test | **Healthy**, 16 abonnements ACK, aucune perte ni violation d’horloge |
| Arrêt demandé | **Code 0**, `operator_stop`, aucun OOM |
| Fenêtres réelles assemblées | **37**, à partir de 896 carnets publics |
| Relecture sur serveur | Même SHA-256 des fenêtres que l’assemblage en cours d’exécution |
| Campagne serveur | **18 variantes exécutées**, verdict scientifique `DATA_BLOCKED` |
| Ressources du service testé | 63,06 s de durée, 1,40 s CPU, 37,64 Mio RSS au pic |
| Isolation | UID/GID 1000, racine read-only, capabilities supprimées, aucun privilège supplémentaire |
| Politique de redémarrage | `no` ; aucun ancien bot redémarré |

Le premier essai serveur a découvert une course lors d’un arrêt demandé pendant
le sommeil du superviseur. Le collector terminait normalement mais le
superviseur le classait comme une sortie inattendue. La correction et son test
de régression font partie de la release ci-dessus ; un nouvel arrêt réel a
confirmé le code 0. Le run en échec demeure distinct et ses données ne sont pas
présentées comme une session financière réussie.

## Preuves

- [État healthy enregistré](health_running.json).
- [Résultat final du service](runtime_result.json) et [manifest de session](runtime_manifest.json).
- [État arrêté](status_stopped.json) et [isolation/état Docker](server_state.json).
- [Relecture et jointure](prepare.json), [campagne de 18 variantes](replay_summary.json).
- [Manifest du déploiement](deployment_manifest.json), identique aux fichiers locaux livrés.

Chaque JSON possède son SHA-256 voisin. Le champ `collector` du dernier statut
contient la dernière mesure prise pendant le fonctionnement ; `state=STOPPED`
et `operational_healthy=false` décrivent l’état final du processus.

## Limite économique conservée

Le service est exécutable et sa chaîne de données fonctionne. Les spécifications,
frais effectifs, références/calibrations et preuves de file nécessaires au
candidat ne sont pas tous qualifiés. Les 37 fenêtres restent donc impropres à
publier un PnL maker validé. Une fin de processus propre n’est pas un PASS OOS,
et aucun ordre réel n’est envoyé.

Le service public n’invente ni référence de settlement, ni calibration entraînée,
ni permission de file. `prepare` permet de joindre les preuves externes lorsqu’elles
existent ; cela ne qualifie pas automatiquement leur contenu. La suite économique
reste celle décrite dans le plan et ne se résout pas par une collecte indéfinie.

## Utilisation

```bash
/opt/hyperbot2/current/bin/hyperbot2-server start 900 300
/opt/hyperbot2/current/bin/hyperbot2-server status
/opt/hyperbot2/current/bin/hyperbot2-server health
/opt/hyperbot2/current/bin/hyperbot2-server stop
```

La première commande autorise au plus 15 minutes, et s’arrête après 5 minutes
si les inputs restent bloqués. Voir [le guide serveur](../../docs/SERVER.md).
