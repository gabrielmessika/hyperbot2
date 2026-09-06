# Expérience bornée BTC — résultat du 6 septembre 2026

**Verdict : DATA_BLOCKED. Étape de faisabilité exécutée et close.**
Aucun backtest économique lancé, aucun PnL calculé et aucune validation de
+30 % mensuels. La campagne ne continue pas automatiquement en calibration/OOS.
Le budget de deux journées de diagnostic est un plafond ; les trois contrôles
complets suffisent à établir le blocage sans le consommer entièrement.

## Exécution réelle

Run : `bounded-20260906T145628Z`. Inputs A clos des 1er, 2 et 3 septembre,
fixtures, datasets, manifests et readiness contrôlés contre leurs sidecars
SHA-256. Les fixtures embarquées ont été relues par le parser strict.
Le code de diagnostic utilise le planner Strategy/Risk existant et la même
fonction de preuve de file que la readiness. C'est une condition nécessaire
sur les quotes planifiées à partir des portefeuilles des fixtures, pas un
backtest fermé avec réinjection des fills.

Trois variantes 6/8/10 bps, 18 lignes de résultat par journée couvrant deux
modèles et trois scénarios. La file initiale est indépendante du modèle de
fill ; les comptes sont donc partagés entre central et pessimiste. Le stress
frais du runner change le coût d'exécution, pas les quotes : il partage ici
les comptes de base. Aucun fill central/pessimiste n'a été inventé.

## Résultats cumulés

Chaque variante émet 250 308 quotes approuvées sur les trois journées.

| Demi-spread minimal | Preuve à l'activation, base | Latence x2 | Quotes derrière le best à la décision |
|---|---:|---:|---:|
| 6 bps | 27 459 / 250 308 (10,97 %) | 10,37 % | 246 069 (98,31 %) |
| 8 bps | 25 296 / 250 308 (10,11 %) | 9,63 % | 248 397 (99,24 %) |
| 10 bps | 24 310 / 250 308 (9,71 %) | 9,31 % | 249 437 (99,65 %) |

Les hashes des prix/tailles effectivement émis sont distincts entre variantes
pour chacune des trois dates. Les frais observés sont 1,44 bps ; le plancher
stratégie vaut 4,88 bps. Les variantes proposées dépassent ce plancher.

La gate existante exige une preuve pour chaque quote. Les exemples montrent
notamment un L2 âgé de 219 ms à la décision qui atteint 569 ms après 350 ms
de latence : il est alors trop ancien pour le seuil de 500 ms. Pour 6 bps,
16 787 des 27 815 quotes avec preuve à la décision la perdent à l'activation
(60,35 %). Sous latence x2, 24 349 la perdent (87,54 %).

Cela réfute la suffisance du filtre simple « preuve présente à la décision ».
Cela ne réfute pas toute stratégie d'abstention possible. Choisir uniquement
les quotes dont la preuve se révèle valide après la décision utiliserait une
information future et n'est pas une solution admissible.

## Décision et prochaine condition de reprise

Arrêter cette campagne avant les rendements. Les données A actuelles ne
qualifient aucune de ces variantes pour un backtest central/pessimiste.
Les périodes futures ne sont ni lancées ni surveillées automatiquement.

Une reprise doit d'abord améliorer la preuve de profondeur L2 à la cadence
nécessaire, ou définir et tester une nouvelle règle causale d'émission avec
marge de fraîcheur tenant compte de la latence. Un changement de cadence de
collecte demande un contrôle de charge et de stockage ; aucune modification
collector n'a été faite ici. Changer le seuil de fraîcheur ou supprimer les
périodes défavorables ne fait pas partie de cette reprise.

## Ressources, intégrité et impact

- 244,04 secondes CPU cumulées (0,068 CPU-heure) ; 242,88 secondes cumulées
  dans les scripts, hors orchestration. Le traitement est limité à 1 CPU.
- Pic RSS 2 428 512 Kio, environ 2,32 Gio ; limite Docker 4 Gio sans swap.
- Trois conteneurs sans réseau, sans secrets, root filesystem read-only,
  inputs read-only, capabilities retirées, sans restart policy.
- Limites CPU et temps par processus de 7 200 s ; trois jours séquentiels
  plafonnent le diagnostic à six CPU-heures, sous le budget global de 24 h.
- Trois sorties `exit=2`, toutes `OOMKilled=false`. Rapports copiés localement
  et SHA-256 revérifiés ; trois variantes consignées dans le journal chaîné.
- Code exact conservé dans l'archive serveur `source.tar`, identifiée par
  `launch.json`, en complément du SHA Git du dépôt qui contient des changements.
- Collecte/evidence/observer healthy après les calculs, zéro restart Docker ;
  scheduler quotidien toujours suspendu. Aucun impact sur le format des raws.
- Validation : 212 tests existants + 3 nouveaux tests (checksums manquants ou
  corrompus, expiration et causalité de la preuve), lint et mypy réussis.

Les JSON journaliers, leurs sidecars, logs, états Docker, `summary.json`,
`launch.json` et `variants.jsonl` accompagnent ce rapport. Le snapshot de code
complet reste sous le répertoire serveur du run, sans copie des raws dans Git.
