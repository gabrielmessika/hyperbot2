# Diagnostic de faisabilité — 6 septembre 2026

**Décision : NO-GO pour poursuivre le maker HIP-4 avec le flux public actuel et
les règles actuelles.** L’exécutable fonctionne, mais ses entrées ne permettent
pas de qualifier une exécution maker. `DATA_BLOCKED` est justifié. Collecter un
mois supplémentaire avec ce même schéma ne reconstituerait pas les informations
de file absentes. Cette décision ne démontre ni l’absence d’edge sur HIP-4, ni
l’impossibilité d’un autre dispositif. Aucun rendement mensuel n’est validé.

## Mesures sur les captures existantes

Aucune nouvelle collecte permanente. Réutilisation du témoin local de 40 s et
du run serveur `hb2-run-1788713353331737536` (63,06 s de runtime), release
`b44a0baa421ac7f2`. Les deux captures portent sur huit coins, quatre paires
YES/NO. Les sommes de contrôle serveur et les hashes de chaque événement brut
ont été vérifiés. Environ 1,36 Mo de fichiers existants ont été rapatriés.

| Mesure | Local | Serveur |
|---|---:|---:|
| Snapshots L2, tous `fast=true` | 591 | 896 |
| Âge apparent à réception : minimum | 193 ms | 336 ms |
| Âge apparent à réception : médiane | 268 ms | 387 ms |
| Âge apparent à réception : p95 | 503 ms | 707 ms |
| Âge apparent à réception : maximum | 1 087 ms | 1 014 ms |
| Carnets frais à réception, ≤ 500 ms | 560/591 (94,8 %) | 792/896 (88,4 %) |
| Intervalle médian des timestamps exchange, par coin | 539 ms | 540 ms |
| Temps où le dernier carnet reçu reste frais | 41,2 % | 17,8 % |
| Admissibles avec placement 350 ms + incertitude 50 ms | 0/591 | 0/896 |

La couverture temporelle additionne les durées par coin, entre sa première et
sa dernière réception : 128 550/311 930 ms localement et 85 812/483 233 ms côté
serveur. Ce n’est ni le taux de disponibilité du portefeuille, ni une estimation
de rentabilité. Les observations des huit coins sont corrélées. Aucune durée
inconnue après la dernière réception n’est ajoutée.

Le démarrage n’explique pas le résultat : après retrait du premier snapshot de
chaque coin, les médianes sont 267 ms et 387 ms, les p95 442 ms et 650 ms.
Les résultats complets restent publiés, sans exclusion des mauvais épisodes.

**Exposition : 0/36 fenêtres complètes passent la fraîcheur sur toute leur durée.**
La 37e fenêtre est incomplète après arrêt et reste signalée séparément.
Sur les fenêtres complètes, le maximum d’âge du dernier carnet connu va de
899 à 1 249 ms, pour une exposition théorique de 1 350 ms (TTL 1 000 + annulation
350). Même en limitant l’examen à partir d’une activation à +100 ou +350 ms,
aucune ne passe. Il s’agit d’un calcul contrefactuel de condition nécessaire :
aucune quote ni aucun fill n’a été approuvé pour cette mesure.

## Les 350 ms sont une hypothèse, pas une mesure d’ordre

La valeur existe déjà dans `hyperbot/config/hyperbot_backtest.example.json:53`.
Sa provenance est enregistrée dans `server_readonly_check.json`. Aucun journal
d’envoi/ACK d’ordre n’a été trouvé pour étalonner cette valeur. Les anciennes
mesures de RTT d’une requête publique ne mesurent pas une activation d’ordre.

Le garde-fou actuel impose `âge + placement prudent + incertitude ≤ 500 ms`.
Avec 350 + 50 ms, il ne reste que 100 ms d’âge admissible. Les deux captures
échouent donc mécaniquement. Aucune erreur d’unité n’a été identifiée dans
`OutcomeBook.age` et le garde-fou de `SelectiveOutcomeStrategy`.

| Placement hypothétique, incertitude maintenue à 50 ms | Local : carnets passant | Serveur : carnets passant |
|---|---:|---:|
| 0 ms | 560/591 | 744/896 |
| 50 ms | 552/591 | 596/896 |
| 100 ms | 544/591 | 24/896 |
| 150 ms | 480/591 | 0/896 |
| 200 ms | 185/591 | 0/896 |
| 350 ms | 0/591 | 0/896 |

Ce tableau ne justifie aucun changement de configuration : il isole la
sensibilité d’un seul garde-fou. La fraîcheur pendant l’exposition et la preuve
de file resteraient manquantes même si l’admission initiale devenait possible.

Horloge : au contrôle serveur à 17:12 UTC, NTP est synchronisé ; offset affiché
+1,282 ms, jitter 2,227 ms, distance racine 31,188 ms. Pendant la capture, l’écart
entre horloge murale et monotone varie d’environ 1,015 ms sur le serveur, contre
55,38 ms localement. Ces mesures ne prouvent pas l’offset absolu à l’heure de la
capture ni l’exactitude de l’horloge exchange ; l’écart entre deux lectures peut
aussi inclure une interruption du processus. Les âges sont donc apparents.
Les témoins n’étant pas simultanés, on ne peut attribuer leur différence au seul
hébergement. Aucune mesure d’ordre réel n’a été faite.

## Les autres causes de `DATA_BLOCKED`

| Condition | Preuve actuelle | Travail nécessaire |
|---|---|---|
| File maker et priorité duale | Les niveaux bruts contiennent seulement `px`, `sz`, `n` | Ordres individuels, transitions, fills et reconstruction contrôlée YES/NO |
| Profondeur au prix coté | Snapshots limités ; `full_depth=false` | Couvrir le prix pendant toute l’exposition ; bloquer les sorties de profondeur |
| Frais et spécification | `fees`, `tick`, `size_increment`, settlement et hash de spécification non qualifiés | Sources datées par marché, validité temporelle, fixture d’exemples calculés |
| Référence causale | `fair=null` dans les fenêtres serveur | Joindre une référence connue à la décision, documenter son modèle et sa fraîcheur |
| Latences placement/annulation | Hypothèses 350/350 ms | Conserver explicitement leur statut hypothétique ; aucune qualification live avec un simple ping |

Exemple d’ambiguïté L2 : deux files peuvent avoir le même prix, le même volume
et le même nombre d’ordres, mais une réduction de volume peut provenir d’un ordre
devant ou derrière notre ordre théorique. Sans identité et transitions, son
effet sur notre rang ne peut pas être établi. Les trades seuls n’identifient pas
toutes les annulations. Les archives HyperBot/Trident/BOT05 déjà inventoriées
restent utiles à la pré-recherche, sans qualification automatique des fills.

## Sources alternatives et coût

Les informations fournisseur ci-dessous ont été consultées le 6 septembre 2026.

| Source | Ce qu’elle apporte | Décision |
|---|---|---|
| Captures legacy et L2 public actuel | Recherche de prix, fixtures, exploration optimiste | Réutiliser ; insuffisant pour lever les gates maker |
| Archives Hyperliquid | L2 historiques et fichiers de fills ; disponibilité non garantie | Pas de chaîne HIP-4 de file initiale + transitions qualifiée identifiée |
| Nœud Hyperliquid autonome | Accès aux données fines et snapshots d’état | Inadapté au serveur actuel |
| QuickNode L4 gRPC | Support HIP-4 documenté, ordres individuels, snapshot puis diffs par bloc | Candidat à un test technique borné ; aucune qualité mesurée ici |

Les archives officielles décrivent des snapshots L2, un chargement environ
mensuel pouvant comporter des trous, et des archives de fills distinctes. Cela
ne constitue pas à lui seul un historique maker HIP-4 immédiatement exploitable.
[Documentation Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data).

Le nœud non validateur recommande 16 vCPU, 128 Go RAM et 500 Go SSD. Le serveur
dispose de 4 vCPU, environ 7,6 Gio RAM et 75 Go de disque, dont 42 Go libres.
Le faire tourner ici n’est pas une option adaptée.
[Dépôt officiel du nœud](https://github.com/hyperliquid-dex/node).

QuickNode documente les coins HIP-4 `#N`, les identifiants d’ordre, timestamps,
hauteurs de bloc, snapshots et diffs. Les snapshots de remplacement sont
autoritaires, notamment lors de changements de priorité ; les trier simplement
par timestamp pourrait perdre l’ordre fourni. La représentation duale et la
reconstruction doivent être vérifiées sur de vraies données.
[Contrat L4](https://www.quicknode.com/docs/hyperliquid/datasets/l4-book).

Le plan Build affiche **49 $ au tarif mensuel de référence**, 80 millions de
crédits, avec des remises annuelles affichées séparément ; vérifier le montant
mensuel au checkout. L’essai gratuit exclut HyperCore gRPC ; Build autorise cinq
streams simultanés. Commencer par un outcome YES/NO évite de supposer que huit
abonnements L4 seraient inclus.
[Tarifs](https://www.quicknode.com/pricing),
[Accès et limites](https://www.quicknode.com/docs/hyperliquid/pricing-faq).

La page gRPC annonce 10 crédits/0,0165 Mo pour les méthodes OrderBook, tandis
que la page tarifaire générale décrit 10 crédits/0,1 Mo. Retenir provisoirement
le tarif spécifique plus élevé pour estimer le budget, puis vérifier la
facturation réelle. 80 millions de crédits correspondent arithmétiquement à
132 000 Mo à ce tarif, avant toute autre consommation ; le volume HIP-4 effectif
n’a pas été mesuré. Aucun coût total illimité à 49 $ n’est promis.
[Tarification gRPC](https://www.quicknode.com/docs/hyperliquid/grpc-api),
[Tarification générale](https://www.quicknode.com/docs/hyperliquid/pricing).

49 $ représentent 4,9 % du capital initial de 1 000 $. Si cette dépense s’ajoute
aux 20 $/mois d’infrastructure supposés par le bot, obtenir 300 $ nets demanderait
369 $ après frais de trading mais avant infrastructure, hors dépassements et
taxes. Cette arithmétique ne prouve pas que l’abonnement serait non rentable ;
l’edge nécessaire reste inconnu.

## Prochaine étape concrète

Suspendre la campagne maker sur le flux actuel. La seule étape technique retenue
si un accès L4 est disponible est un **test d’entrée sur un seul outcome YES/NO**,
sans ordre : plafond de 30 minutes de capture, 250 Mo bruts et une journée de
travail, arrêt au premier plafond. Aucun abonnement n’a été acheté ni sollicité.

1. Adapter snapshot/diffs au stockage existant ; conserver ordre, hauteur, temps
   exchange/réception, provenance et reset. Réconcilier le carnet reconstruit à
   un snapshot indépendant ; une divergence ou une continuité non démontrable
   invalide l’intervalle, sans suppression opportuniste des erreurs.
2. Vérifier explicitement les deux représentations et les transitions de
   priorité. Mesurer âge et couverture sur toute l’exposition, avec les règles
   actuelles et les hypothèses de latence clairement identifiées. Une absence
   d’événement sur un filtre ne doit pas devenir une fausse preuve de continuité.
3. Mesurer octets et crédits, extrapoler prudemment le coût ; arrêter si les
   plafonds ou la couverture demandée ne sont pas tenables.
4. Un résultat technique favorable autoriserait seulement la suite de la
   recherche : frais/spécification datés, référence causale puis replay central
   et pessimiste. Le passage hors `DATA_BLOCKED` exige toutes ces preuves.
   La validation économique hors échantillon resterait ensuite à produire.

Sans accès qualifiable et budget explicite pour cette branche, le maker reste
en NO-GO. Une éventuelle stratégie à horizon plus long constituerait une nouvelle
thèse à évaluer ; les données actuelles ne suffisent pas à la recommander rentable.

## Reproduction et livraison

Analyse : `scripts/diagnose_feasibility.py`. Quantiles par rang supérieur ;
intégration de fraîcheur entre réceptions successives du même coin ; seuil
500 ms ; contrôle contrefactuel des fenêtres à TTL 1 000 + annulation 350 ms.
Les traces source, configurations et versions du collector figurent dans les
JSON. Les octets bruts restent hors Git dans `data/` et sur le serveur.

```bash
rtk proxy uv run python scripts/diagnose_feasibility.py \
  --raw data/feasibility_2026-09-06/server_capture/raw/outcomes-fast-public.jsonl \
  --windows data/feasibility_2026-09-06/server_capture/windows.jsonl \
  --output tmp/feasibility-server-rerun.json
```

L’output doit être nouveau ; les rapports ne sont pas écrasés. Preuves publiées :
[serveur](server_diagnostic.json), [local](local_diagnostic.json),
[provenance des fichiers](input_manifest.json),
[contrôle serveur en lecture seule](server_readonly_check.json), tous avec SHA-256.

152 tests passent, dont trois tests de calcul de fraîcheur ; lint et typage
strict vérifiés. Aucun changement du runtime, de ses paramètres, du déploiement
ou du format brut. Aucun conteneur actif au contrôle final du serveur.
