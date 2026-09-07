# HyperBot2

Implémentation autonome du [plan](STRATEGY_IMPLEMENTATION_PLAN.md) : recherche
et simulation d’un maker sélectif sur les outcomes quotidiens BTC, ETH, SOL et
HYPE. Capital de référence : 1 000 $. Le [rapport de validation](reports/implementation_2026-09-06/REPORT.md)
sépare les tests logiciels des preuves économiques encore manquantes.

**Version 0.2.0 : exécutable serveur, service public borné, healthcheck et
assemblage automatique des captures.** Voir [l’exploitation serveur](docs/SERVER.md)
et [le rapport d’acceptation](reports/server_2026-09-06/REPORT.md).

Le noyau HyperBot est repris dans ce dépôt : collector, stockage vérifiable,
adaptateurs legacy, moteur de file, superviseur de risque et outils statistiques.
Voir la [provenance et les adaptations](reports/reuse/README.md).
Il n’existe aucune dépendance runtime vers les trois anciens dépôts.

## Installation et démonstration locale

Python ≥ 3.11, `uv` ; `curl` uniquement pour la découverte publique du témoin.
Depuis la racine du dépôt :

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run mypy src

uv run python scripts/make_demo.py --output tmp/demo-input
uv run hyperbot2 replay --input tmp/demo-input/windows.jsonl --output tmp/demo-replay
uv run hyperbot2 shadow --input tmp/demo-input/windows.jsonl --output tmp/demo-shadow
```

La démonstration est **entièrement synthétique** : ses prix, frais, hashes de
spécification et qualifications de file sont des fixtures de test. Ses profits
éventuels ne renseignent pas sur la rentabilité du bot. `shadow` applique le
même moteur aux fenêtres enregistrées ; il ne lance pas un service permanent
sur un compte. Les dossiers de sortie doivent être nouveaux à chaque exécution.

## Réutiliser les données existantes

Le screening ouvre les archives explicitement désignées, en lecture seule,
sans recopier les gros fichiers. Exemple dans le workspace actuel :

```bash
uv run hyperbot2 screen \
  --books /workspaces/trident/server-data/hip4/logs/hip4_nautilus_shadow/book_snapshots.jsonl \
  --settlements /workspaces/trident/server-data/hip4/logs/hip4_outcome_mainnet_paper/settlements.csv \
  --output data/screen-001
```

`--max-records 1000` permet un diagnostic borné ; le rapport indique alors que
le scan est partiel. Les hashes source, période, adaptateur, exclusions,
profondeur à 10 $, vieillissement, spreads et markouts descriptifs sont publiés.
Les snapshots B et le paper legacy ne deviennent jamais des fills maker A.
Les importeurs/checksums et formats historiques d’HyperBot restent disponibles
dans `hyperbot2.legacy`, sans dépendance à son installation.

## Découverte publique et qualification

```bash
uv run hyperbot2 witness --seconds 40 --public-network --output data/witness-001
uv run hyperbot2 catalog \
  --input data/witness-001/outcome_meta.json \
  --observed-ms 1788710908498 \
  --output data/catalog-001
```

Remplacer `--observed-ms` par le champ `observed_ms` du témoin concerné.
Le témoin s’arrête seul après 1 à 3 600 secondes. Il souscrit les côtés YES/NO
en `l2Book fast=true` et les trades publics, conserve les ACK, incidents et
trois horloges, puis calcule la fraîcheur à réception et à activation.
Une profondeur de cinq niveaux n’est jamais déclarée complète.

Le catalogue découvre les marchés mais exige une attestation causale explicite
pour les ticks/lots, le statut, la règle de settlement et les taux effectifs.
Le schéma de `--attestations` et celui des fenêtres sont décrits dans
[DATA_CONTRACT.md](docs/DATA_CONTRACT.md). Un hash identifie une preuve ; il ne
démontre pas à lui seul sa qualité. Aucune valeur actuelle n’est appliquée
rétroactivement à une archive.

## Simulation et limites

Une campagne preregistre trois marges, deux modèles (central/pessimiste) et
trois scénarios (base, frais ×2, latences ×2), soit 18 exécutions. Avec
`--model optimistic_touch`, elle exécute neuf plafonds optimistes exploratoires.
Les entrées JSONL sont lues en streaming et vérifiées avant/après lecture.
Les historiques de cycles/fills restent en mémoire sous le plafond du processus.
Un dépassement de budget invalide le run ; il ne tronque pas silencieusement
les résultats. Plafonds : 24 h CPU, 4 Gio mémoire, 10 Gio de sorties cumulées.

La stratégie ne cote que la représentation YES, financée en cash, sans vente
nue ni split/merge. Elle prend en compte les réservations, les ventes partielles,
les frais par opération et la liquidation terminale à profondeur visible ; le
reliquat non liquidable vaut zéro. Le modèle central place toute la quantité
visible devant l’ordre. Les copies duales d’un trade sont dédupliquées.

La limite d’actions de recherche réserve dès l’émission une action de placement
et une annulation. Ce compteur simulé n’atteste pas le quota d’un compte réel.
Les caps de la fondation et la limite de fraîcheur de 500 ms restent actifs.
Une campagne interrompue conserve son diagnostic et ne reprend pas avec un
portefeuille fictivement réinitialisé : la reprise de session n’est pas implémentée.

Le service `run` marque une interruption non finalisée au démarrage suivant.
Chaque nouvelle session possède un identifiant distinct ; ses résultats ne
sont jamais raccordés artificiellement au capital d’une session interrompue.
Le redémarrage automatique est désactivé. Les arrêts SIGTERM/SIGINT finalisent
les fenêtres, les rapports et les checksums avant de sortir.

Les commandes retournent `0` si le traitement finit sans blocage de données
(ce n’est pas un PASS économique), `2` pour `DATA_BLOCKED`, et un code non nul
avec `failure.json` pour une erreur d’exécution après création du run.
Tous les rapports excluent une promotion automatique.

## État opérationnel

Le [suivi](FOLLOW_UP.md) liste les livraisons et les conditions restantes.
Le dépôt ne contient aucune passerelle signant ou envoyant des ordres réels.
`live_enabled=true` est refusé par la configuration. Le déploiement HyperBot2
sur serveur a été explicitement demandé après la livraison initiale. Il reste
séparé des anciens bots, qui ne sont pas redémarrés.
