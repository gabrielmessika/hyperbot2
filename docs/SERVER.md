# Exploitation HyperBot2 0.2.0

Installation indépendante : `/opt/hyperbot2`. Les releases sont identifiées
par le hash de leur contenu. `current` sélectionne la release installée ;
`shared/data` conserve les captures, fenêtres, manifests et rapports.
Le paquet fonctionne sous Docker, sans installation Python des anciens bots.

## Commandes sur le serveur

```bash
/opt/hyperbot2/current/bin/hyperbot2 --version
/opt/hyperbot2/current/bin/hyperbot2-server start 900 300
/opt/hyperbot2/current/bin/hyperbot2-server health
/opt/hyperbot2/current/bin/hyperbot2-server status
/opt/hyperbot2/current/bin/hyperbot2-server logs
/opt/hyperbot2/current/bin/hyperbot2-server stop
```

`start 900 300` lance une session de 15 minutes maximum, interrompue après
5 minutes si des blocages de données persistent. Sans arguments, ces mêmes
bornes s’appliquent. La durée maximale admise est 24 heures, sans renouvellement
automatique. Le service s’arrête également à l’expiration du catalogue observé.
Un second démarrage est refusé si l’instance tourne déjà ; un verrou sur les
données protège aussi contre les démarrages concurrents par la CLI.

Le service souscrit les carnets rapides et trades YES/NO des quatre sous-jacents,
persiste les événements HyperBot, assemble les fenêtres et les transmet aux
moteurs central et pessimiste. Les données publiques ne reçoivent aucune
qualification de file inventée. Les décisions s’abstiennent si les preuves
de spécification, frais, référence ou exécution manquent.

## Lire l’état correctement

Le JSON distingue :

- `state` : `STARTING`, `RUNNING`, `STOPPING`, `STOPPED` ou `FAILED` ;
- `operational_healthy` : connexion, ACK, horloge, absence de pertes et activité
  récente ; le healthcheck refuse aussi un heartbeat vieux de plus de 15 s ;
- `research.verdict` et `research.blockers` : état scientifique et compteurs
  des inputs manquants, distincts de la disponibilité du processus.

`RUNNING` et un healthcheck positif peuvent donc coexister avec `DATA_BLOCKED`.
Un arrêt normal pour budget de données sort avec le code **0** et une raison
explicite, sans prétendre que la stratégie est validée. Une panne sort en erreur.
L’arrêt Docker/SIGTERM finalise le rapport ; un kill brutal invalide le PnL
non finalisé et est signalé lors du prochain démarrage, sans prétendre reprendre
un portefeuille réel. Aucun ordre réel n’existe dans cette application.

Les durées, limites, version du code et configuration sont figées dans le
`manifest.json` de chaque run. Les raws restent append-only. La dernière fenêtre
incomplète est conservée avec `exposure_healthy=false` ; elle ne disparaît pas
pour améliorer les résultats.

## Relecture et jointure des captures

Lire le champ `output` de `status` pour connaître le chemin `/data/runs/...`.
Les chemins vus par les commandes Docker sont ceux du conteneur :

```bash
/opt/hyperbot2/current/bin/hyperbot2 prepare \
  --capture /data/runs/RUN_ID \
  --output /data/prepared/PREPARE_ID

/opt/hyperbot2/current/bin/hyperbot2 replay \
  --input /data/prepared/PREPARE_ID/windows.jsonl \
  --output /data/campaigns/CAMPAIGN_ID
```

Chaque répertoire de sortie doit être nouveau. `prepare` fonctionne aussi
localement sur une capture `witness` de la v0.1. Les checksums des raws et de
leurs payloads sont vérifiés, ainsi que leur stabilité pendant la préparation.

`prepare --attestations /data/imports/attestations.json --references
/data/imports/references.jsonl` permet la jointure des preuves externes. Chaque
fichier doit avoir son voisin `.sha256`. Les références sont triées par instant
de réception, avec champs `kind="settlement_mark"`, `underlying`, `exchange_ms`,
`received_ms`, `price` (chaîne décimale) et `source_sha256`. Elles alimentent
le modèle uniquement lorsqu’elles sont disponibles à la décision. Les preuves
de source et de calibration restent à auditer ; fournir un hash n’établit pas
leur validité économique. Le service public lui-même ne fabrique pas une
référence de settlement à partir d’un midpoint quelconque.

## Déploiement reproductible

Depuis le dépôt local :

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run mypy src
uv run python scripts/deploy.py
```

Le script construit le wheel, exporte les dépendances verrouillées avec leurs
hashes, transfère uniquement une liste explicite de fichiers et vérifie leurs
SHA-256 côté serveur. Il construit/teste l’image avant de changer `current`.
Il ne démarre aucun conteneur. Une release existante n’est pas écrasée.
La cible SSH par défaut reprend la configuration existante ; les options
`--host`, `--user`, `--identity` permettent de la spécifier.

Pour revenir à une release précédente : arrêter HyperBot2, repointer `current`
vers son répertoire dans `releases`, puis utiliser son script de démarrage.
Les données partagées ne sont ni supprimées ni réécrites par le déploiement.
Un rollback logiciel ne restaure pas un ancien état économique.

## Isolation et ressources

Le conteneur utilise l’UID/GID 1000, un système de fichiers racine en lecture
seule, aucune capability, aucun port publié et aucune clé de trading. Seuls
ses propres fichiers dans `shared/data` sont montés en écriture. Les limites
sont 4 Gio RAM, un CPU, 128 processus et 10 Gio de données cumulées contrôlés
par l’application. Les logs Docker tournent sur trois fichiers de 10 Mo.
`restart=no` évite les boucles de collecte et les reprises involontaires.
