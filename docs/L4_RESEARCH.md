# Tester la piste L4 sans ordre

Le maker reste `DATA_BLOCKED`. Cette sonde vérifie uniquement que des snapshots
L4 et des diffs HIP-4 peuvent être récupérés puis réconciliés. Elle ne qualifie
pas automatiquement la priorité duale, les fills, la fraîcheur historique à
réception, l’OOS ou une promotion. Elle ne contient aucun client d’ordre.

## Accès nécessaire

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
