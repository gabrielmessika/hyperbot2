# Rebond après liquidations BTC/ETH — 7 septembre 2026

**Décision : `INSUFFICIENT_SAMPLE`. Aucun avantage rentable démontré, aucun GO.**
La piste est désormais testable avec les données accessibles, mais ce pilote
ne permet ni de confirmer ni de rejeter le mécanisme général. Ne pas construire
un bot d'exécution sur ce résultat et ne pas modifier les seuils pour créer des trades.

## Ce qui a été vérifié

La clé 0xArchive existante donne accès aux liquidations brutes, à leurs volumes
horaires et à l'open interest BTC/ETH. Audit initial sur le 5 septembre :
81 lignes BTC, 29 ETH ; volumes et nombres concordants dans la fenêtre
semi-ouverte. Les agrégats renvoient aussi le bucket de borne finale : il est
exclu, sinon la comparaison serait fausse. La route de couverture a une
enveloppe différente des séries, désormais prise en charge explicitement.

Le protocole principal, enregistré avant téléchargement, prévoyait 180 jours
avec 30 jours de chauffe. Première requête ancienne refusée HTTP 403
`history_window_exceeded` : accès limité aux **30 derniers jours**, frontière
annoncée le 8 août 2026 vers 09:00 UTC lors de l'appel. La campagne 180 jours
est arrêtée, pas remplacée silencieusement par un backtest favorable.

Un [pilote distinct](PILOT_PROTOCOL.md), enregistré avant téléchargement élargi
et calcul des résultats, utilise les 28 jours complets communs à l'abonnement
et aux prix existants : **9 août–6 septembre exclusif**. Sept jours de chauffe,
21 jours calendaires d'observation, dont les 26 dernières heures ne peuvent
contenir de nouveau signal afin de laisser tous les horizons/stress observables.
La fenêtre de calcul passée est ramenée à sept jours ; les autres seuils sont
inchangés. Il ne s'agit pas de la validation prévue sur 180 jours.

Les OHLC/funding HyperBot2 existants sont réutilisés avec contrôle de checksum
et de continuité ; aucune nouvelle requête de prix. La recherche ciblée dans
le code et les scripts HyperBot n'a trouvé aucun champ de liquidation/OI
permettant de reconstruire directement ces séries. Les anciens dépôts restent
en lecture seule, sans nouvelle dépendance runtime.

## Règle étudiée et taille de l'échantillon

Acheter après une heure où le prix a perdu au moins 0,5 %, avec au moins cinq
liquidations longues et 80 % du volume liquidé du côté long. Ce volume doit
dépasser 100 k$ BTC / 50 k$ ETH et le quantile 95 % des heures longues positives
publiées pendant les sept jours précédents, avec au moins 60 observations.
Espacement de 25 h par actif. Entrée théorique à l'open suivant ; sortie
principale six heures plus tard. Aucune modification après calcul des signaux.

| Donnée sur les 672 heures | BTC | ETH |
|---|---:|---:|
| Heures de volumes publiées, borne finale exclue | 287 | 205 |
| Heures avec volume long positif | 161 | 105 |
| Maximum d'heures longues positives dans un lookback admissible | 70 | 52 |
| Heures candidates avec au moins 60 observations passées | 103 | 0 |
| Buckets OI présents | 672 | 672 |
| Événements retenus | **1** | **0** |

Les heures de liquidation absentes ne sont **pas transformées en zéros**.
ETH échoue ici sur la taille de l'échantillon de référence ; cela ne démontre
pas une absence de liquidations ni une absence générale d'opportunités ETH.

## Résultat descriptif de l'unique événement

BTC, **28 août 2026, 16:00–17:00 UTC** : 18 458 084,09 $ liquidés longs,
contre un seuil passé de 7 760 994,36 $, baisse de prix horaire de 0,695 %.
Trois pages brutes, pagination terminée : **2 535 lignes longues et 30 courtes**,
zéro doublon ; nombres et volumes concordent à moins d'un centime.
Variation entre buckets d'OI en contrats : −0,784 %. Cette variation agrégée
n'est pas une mesure instantanée de l'OI au début du choc.

Entrée hypothétique le 28 août à 17:00 UTC. Un bps = 0,01 % du notionnel
acheté ; ces rendements ne sont pas des performances du capital de 1 000 $.

| Horizon | Brut | Net de base | Net avec coûts stressés |
|---|---:|---:|---:|
| 1 h, secondaire | +15,43 bps | +2,30 bps | −12,71 bps |
| **6 h, principal** | **−3,09 bps** | **−16,77 bps** | **−31,76 bps** |
| 24 h, secondaire | +31,25 bps | +15,46 bps | +0,44 bps |

Base : frais taker 4,5 bps et slippage supposé 2 bps par côté, funding horaire
compté défavorablement en valeur absolue. Stress coûts : 9 + 5 bps par côté.
Entrée et sortie retardées d'une heure : **−18,95 bps** à six heures. Même le
contrôle sans coûts est négatif à six heures. Le barème de frais utilisé est
celui de base publié par [Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees) ;
le slippage reste une hypothèse, pas une mesure d'exécution.

Aucun témoin ne satisfait les critères d'appariement fixés ; impossible
d'isoler un effet propre aux liquidations par rapport à une baisse ordinaire.
Un événement sur un jour : pas d'intervalle bootstrap publié qui donnerait une
fausse précision. Les horizons secondaires positifs ne justifient pas de
remplacer l'horizon principal après inspection. Aucun rendement mensuel extrapolé.

## Limites et décision suivante

- La couverture fournisseur décrit fills/OI/carnets/funding, **pas une série
  de liquidations certifiée sans trous**. Concordance brut/agrégat chez le même
  fournisseur ≠ audit indépendant d'exhaustivité.
- Les champs `liquidator_user` et `liquidated_user` sont identiques sur toutes
  les lignes brutes examinées. Leur sémantique reste à clarifier ; aucune
  identité, aucun PnL de compte ne participe au signal. Les directions et
  montants sont cohérents entre les deux routes, sans preuve native indépendante.
- Historique de pré-recherche de classe B ; ne qualifie ni la disponibilité
  causale du signal, ni des fills, ni une exécution maker. Prix déjà consultés,
  aucun holdout indépendant. Les opens horaires ne constituent pas des fills
  exécutables prouvés ; délais de publication inconnus et stress d'une heure seulement.
- Aucun simulateur de portefeuille ou de risque n'est justifié sur ce seul
  épisode. Aucun résultat ici ne soutient l'objectif de +30 % par mois.

**Prochaine étape utile : obtenir 90–180 jours de liquidations identifiées et
contrôler leur couverture**, puis enregistrer une nouvelle campagne avant de
calculer les rendements supplémentaires. Le protocole 180 jours et ses seuils
restent conservés. L'abonnement actuel ne suffit pas à récupérer cette profondeur
en une fois. Examiner une archive existante ou une extraction native avant
d'envisager un accès payant ; aucun achat engagé. Archiver seulement à partir
d'aujourd'hui prendrait plusieurs mois et ne répondrait pas au besoin immédiat.

Le résultat présent ne justifie ni une nouvelle variante d'indicateurs ni une
relance des bots. Il ne prouve pas non plus qu'un bot Hyperliquid rentable soit
impossible : le manque d'échantillon est distinct d'un rejet économique robuste.

## Livraison et reproduction

Client de données borné sans signature/ordre ; clé transmise par stdin/en-tête,
jamais en argument ou dans les artefacts. Parseur des buckets, sélection causale,
vérification brute, coûts et étude offline livrés. Tests : sparse ≠ zéro,
bornes temporelles, fuite future, directions/doublons, comptabilité, absence
de secret dans argv et rejet d'un écho de clé. **184 tests**, lint, format et
mypy passent. Aucun serveur, service, collecte permanente ou configuration
live modifié. Les anciens bots n'ont pas été relancés.

Acquisition : **16 requêtes**, 15 HTTP 200 et un HTTP 403, **1 698 943 octets**,
9,27 secondes cumulées d'appels, sous les plafonds fixés. Voir
[manifestes et compteurs](acquisition.json). Raws append-only hors Git avec
SHA-256 ; schémas, bornes, transformations, code et protocoles identifiés dans
[le résumé vérifié](final/summary.json) et [l'événement](final/events.json).
Les calculs intermédiaires `results/` et `verified/` sont conservés ; `final/`
est la référence après corrections de lint/format et tolérance d'arrondi du test,
sans changement des résultats. Une seconde reproduction offline produit les
mêmes SHA-256 pour les deux fichiers de résultat.

Depuis `/workspaces/hyperbot2`, destination nouvelle obligatoire :

```bash
rtk proxy uv run python scripts/investigate_liquidations.py --output tmp/liquidation-reproduction
```

Cette commande lit les snapshots locaux et ne requiert ni clé ni réseau.
Contrats fournisseur consultés :
[liquidations](https://docs.0xarchive.io/schemas/operations/get-hyperliquid-liquidations),
[volumes](https://docs.0xarchive.io/schemas/operations/get-hyperliquid-liquidation-volume),
[open interest](https://docs.0xarchive.io/schemas/operations/get-hyperliquid-open-interest).
