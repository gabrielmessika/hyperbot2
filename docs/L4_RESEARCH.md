# Tester la piste L4 sans ordre

Le maker reste `DATA_BLOCKED`. Cette sonde vérifie uniquement que des snapshots
L4 et des diffs HIP-4 peuvent être récupérés puis réconciliés. Elle ne qualifie
pas automatiquement la priorité duale, les fills, la fraîcheur historique à
réception, l’OOS ou une promotion. Elle ne contient aucun client d’ordre.

**Diagnostic maker clôturé le 7 septembre : NO-GO avec le transport actuel.**
Le [rapport final](../reports/maker_final_2026-09-07/REPORT.md) documente le
raccord WebSocket incomplet, sa réparation historique REST et l’insuffisance
de fraîcheur sur deux témoins simultanés. Suspendre la collecte maker dans
ces conditions ; les commandes ci-dessous restent des outils de diagnostic.

## Accès nécessaire

**Mise à jour du 7 septembre : accès fourni et testé avec succès.** La clé de
`keys.txt` est ignorée par Git et protégée en 0600. Une copie protégée est
installée au chemin serveur ci-dessous. Le format brut et la ligne
`OXARCHIVE_API_KEY=...` sont acceptés, sans exécution shell du fichier.
Voir les [résultats mesurés](../reports/l4_2026-09-07/REPORT.md).

Le contrôle du 6 septembre a confirmé HTTP 401 sans authentification sur le
route L4 de 0xArchive. Le fournisseur documente un compte gratuit et une clé
`OXARCHIVE_API_KEY` : [création d’accès](https://docs.0xarchive.io/quickstart),
[limites gratuites](https://0xarchive.io/pricing). Aucun compte ni abonnement
n’a été créé par l’agent. Un petit test doit vérifier les crédits et la couverture
réels avant tout téléchargement plus long.

Conserver uniquement la clé de données dans un fichier protégé hors Git,
par exemple `/opt/hyperbot2/shared/secrets/oxarchive.key`, lisible par
`trident-deploy` uniquement. Ne pas coller la clé dans le chat, dans une commande
ou dans un rapport. La sonde accepte ce fichier via `--key-file`, ou lit la
variable `OXARCHIVE_API_KEY` déjà configurée. La clé est transmise à curl par
stdin ; elle n’apparaît pas dans ses arguments ni dans les manifestes.

## Commande prête

Utiliser le chemin installé indiqué dans `server_research_install.json` du
rapport. Exemple depuis la racine du bundle de recherche :

```bash
bin/hyperbot2-l4-probe \
  --outcome-id 1715 \
  --start-ms 1788710400000 \
  --end-ms 1788710410000 \
  --key-file /opt/hyperbot2/shared/secrets/oxarchive.key \
  --output /opt/hyperbot2/shared/data/l4-archive-test-001
```

Cet exemple cible BTC YES/NO le 6 septembre 2026, de 16:00:00 à 16:00:10 UTC.
Si la fenêtre est hors de l’historique inclus dans le compte, choisir un outcome
et une fenêtre récents à partir des métadonnées. Le répertoire de sortie doit
être nouveau. La sonde n’achète rien et ne crée aucune tâche permanente.

Plafonds : fenêtre de 60 s maximum, 14 requêtes au total, 5 pages de 1 000 diffs
maximum par côté, 2 Mo maximum par réponse et 20 Mo de budget agrégé contrôlé
avant chaque requête (une dernière réponse peut dépasser le seuil agrégé
d’au plus 2 Mo). Timeout de 20 s par requête, aucune relance automatique.
Les pages supplémentaires non lues provoquent un blocage.

## Interprétation

- `DATA_BLOCKED` sans requête : clé absente.
- `DATA_BLOCKED` après requêtes : consulter les codes HTTP, les raws et les
  éventuels résultats partiels. Une erreur, une troncature, un cursor répété,
  une insertion devant un ordre inconnu ou une divergence bloque le résultat.
- `CHECKPOINTS_MATCHED_RESEARCH_ONLY` : les deux reconstructions YES/NO
  correspondent aux snapshots finaux aux checkpoints examinés. Cela reste
  insuffisant pour qualifier ce qui s’est passé entre deux checkpoints.

Le reconstructeur conserve l’ordre de priorité fourni et `insert_before`.
Il refuse les nombres flottants déjà arrondis, les snapshots tronqués, les
diffs en désordre et les hausses de taille dont la priorité n’est pas qualifiée.
Les diffs initiaux/finals hors des blocs couverts sont conservés dans les raws.
Les états intermédiaires d’un bloc peuvent transitoirement se croiser ; les
snapshots réconciliés ne le peuvent pas.

Après un test positif : auditer continuité et références temporelles, joindre
fills/annulations et règles duales, mesurer un flux live de données en lecture
seule, puis reprendre les gates du plan. Aucun simple rapprochement de deux
snapshots ne donne un GO économique.

## Témoin temps réel et audit offline

Depuis un environnement Python 3.11+ synchronisé (`uv sync`), le témoin utilise
le stockage append-only existant et conserve les messages originaux, leur
horloge fournisseur, l’horloge locale et la séquence locale. Exemple historique
du test du 7 septembre (choisir un outcome actif pour une nouvelle mesure) :

```bash
uv run python scripts/witness_archive_l4.py \
  --outcome-id 1896 --seconds 30 --channel hip4_l4_diffs \
  --key-file keys.txt --output data/l4-new-witness
```

Le canal `hip4_l4_orders` permet un témoin distinct des événements de cycle
d’ordre. Il n’a fourni aucun snapshot initial pendant notre test. Les deux
canaux restent en lecture seule : 120 s maximum, arrêt sur gap/erreur,
100 000 messages maximum, aucun reconnect automatique. La clé passe en
en-tête mémoire WebSocket et ne figure pas dans les rapports.

Reproduire le diagnostic livré sans requête ni clé, avec les raws conservés
localement et un nouveau nom de rapport :

```bash
uv run python scripts/audit_l4_evidence.py \
  --data data/l4_2026-09-07 \
  --native data/feasibility_2026-09-06/server_capture/raw/outcomes-fast-public.jsonl \
  --output data/l4-audit-new.json
```

Les fichiers bruts sont nécessaires, ne sont pas versionnés et restent
checksumés. Le script refuse les divergences et compare les reconstructions,
la profondeur duale aux captures natives et les statistiques de fraîcheur.
