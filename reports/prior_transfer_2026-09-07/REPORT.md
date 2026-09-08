# Le transfert2025 échoue : promotion du candidat partagé suspendue

**Le portefeuille cassures/rotation50/50 ne démontre pas un edge généralisable.**
Le test antérieur2025, enregistré avant calcul, perd270,83 $ sur un compte
de 1 000 $ et s'arrête dès le 19 janvier. Même dans le scénario sans frais
ni funding, avec slippage paramétré à zéro et arrondi adverse des ticks
conservé, il perd 264,46 $. Les résultats récents positifs ne suffisent pas pour GO.

Ce test utilise les prix, volumes et fundings Binance d'un sous-panel15,
avec les contraintes économiques de référence Hyperliquid. Ce n'est pas
un résultat natif Hyperliquid2025 inventé. Le changement de plateforme et
d'univers limite la conclusion : la généralisation reste non confirmée,
sans effacer les résultats natifs récents ni prétendre prouver leur futur.

## Acquisition gratuite et sélection avant PnL

Les métadonnées publiques ont retenu15 contrats perpétuels USDT existant
avant le1 janvier2025 : ARB, BNB, DOGE, ENA, FARTCOIN, INJ, JUP, LINK,
NEAR, TAO, UNI, WLD, XMR, XRP, ZEC. LIT, PUMP et XPL n'ont pas un contrat
courant couvrant toute l'année et n'entrent pas dans ce seul transfert.
Aucun remplacement ni retrait selon les gains. Le panel original18 reste
conservé et comparé au sous-panel15 sur les mêmes dates natives2026.

Source : [archives publiques officielles Binance](https://github.com/binance/binance-public-data).
360 ZIP mensuels (bougies1h et funding), tous vérifiés contre CHECKSUM
fournisseur et SHA-256 local. 721 requêtes publiques au total,7 468 429 octets,
aucune clé et0 $ de données. Le code exact d'acquisition avant correction
de présentation est archivé et checksumé ; pas d'édition pendant son exécution.

Pour chaque actif :8 760 bougies, aucun trou, zéro heure à volume nul.
ENA/FARTCOIN/JUP/TAO :2 190 fundings, intervalle4h ; les onze autres :1 095,
intervalle8h. Offsets maximum16–20ms après l'heure. Chaque intervalle est
vérifié avant insertion des heures sans paiement à zéro. Les taux absents
ne sont pas imputés arbitrairement à zéro. Aucun actif n'a dû être éliminé
après le contrôle de couverture. ClasseC, adaptateur reproductible.

## Résultats du candidat sur l'année2025

Règles inchangées : budgets50/50, exposition cible1,5x, horizons24/168h,
compte natif simulé avec ordres différés et ticks adverses, arrêt global30 %.
Les comptes restent arrêtés après le déclenchement, sans reprise ni clipping.

| Scénario sans infrastructure supplémentaire | PnL terminal | Drawdown observé | Enveloppe prudente |
|---|---:|---:|---:|
| Central | −270,83 $ | 31,40 % | 38,88 % |
| Coûts renforcés | −262,08 $ | 30,29 % | 33,45 % |
| Entrées retardées | −298,88 $ | 33,24 % | 38,03 % |
| Funding adverse | −257,73 $ | 30,13 % | 33,34 % |
| Zéro coût descriptif | −264,46 $ | 31,08 % | 38,56 % |

Les cinq s'arrêtent le19 janvier, à des heures différentes. Le résultat
moins négatif du stress de coûts n'est pas un avantage des frais élevés :
ils modifient le dimensionnement et avancent l'arrêt de risque de huit heures.

Central :110 ordres et46 épisodes natifs. Deux épisodes FARTCOIN perdent
136,97 $ et116,93 $, puis un épisode ENA26,31 $. Frais totaux5,14 $ et
funding net débité0,60 $ : le problème principal est l'exposition au mouvement
de prix, pas la facture d'exécution. Aucun actif n'a été retiré après cela.

La sensibilité hypothétique20 $/30jours donne−496,10 $ central et−539,57 $
avec retard. L'infrastructure est débitée pendant toute l'année, même après
l'arrêt ; ses coûts atteignent243,33 $. Ce n'est ni une facture réelle ni
une perte de trading intégralement attribuable aux positions. Tous les cas
terminent sans position, mais aucun ne passe le filtre risque/rendement.

## Comparateurs passifs et effet d'univers

Comparateurs prédéfinis : achat équipondéré unique après193 heures de warmup,
quantités conservées jusqu'au dernier open ou à l'arrêt, sans rééquilibrage.

| Panneau, central sans infra | Candidat1,5x | Passif0,5x | Passif1,5x |
|---|---:|---:|---:|
| Hyperliquid18,204 jours2026 | +538,26 $ | +292,53 $ | −30,74 $ |
| Hyperliquid15, mêmes dates | +358,82 $ | +258,98 $ | +23,84 $ |
| Binance15, année2025 | −270,83 $ | −244,20 $ | −158,08 $ |

Le passif0,5x sur2026 est moins coûteux et moins risqué que le candidat actif :
3,85 % mensuels équivalents et16,98 % d'enveloppe sur18 actifs. Sous coûts
renforcés, il garde291,54 $, contre206,49 $ pour le candidat. Mais presque
tout son gain récent provient d'août et du début septembre. En2025 il
s'arrête le6 avril, drawdown observé30,22 %, enveloppe31,03 %. Le passif1,5x
s'arrête dès le27 janvier, drawdown observé31,93 %. Aucun contrôle passif
n'est donc promu comme solution robuste après cette comparaison.

Le candidat actif sur15 actifs natifs2026 reste positif, mais dépasse déjà
30 % d'enveloppe sous coûts renforcés32,18 % et retard34,49 %. Il faut donc
distinguer effet du sous-panel et effet de période/plateforme. Détails et
incertitude descriptive : [comparaison native](NATIVE_COMPARISON.md).

## Décision et prochaine piste

Statut : **SHARED_STRATEGY_GENERALIZATION_NOT_CONFIRMED**. Promotion suspendue.
Pas de GO ni de rendement net10 % démontré. Les fichiers historiques positifs
restent des preuves d'une période explorée, pas une espérance future validée.

Changer de mécanisme plutôt que retirer FARTCOIN/ENA ou régler un seuil sur
le19 janvier : prochaine hypothèse, tendance plus lente avec répartition
des tailles selon la volatilité passée, cap global fixe et aucune augmentation
de levier pour rattraper les pertes. Les périodes2025 et2026 seront utilisées
dès le départ comme épreuves distinctes, avec leurs limites de plateforme.
Enregistrer les règles avant calcul et conserver tous les échecs. Une variante
choisie après cette étude ne sera pas présentée comme validée hors échantillon.

Les prix de fill restent des proxies open+slippage à open+60s, sans carnet
historique ni preuve de fills partiels. Le funding est valorisé au prix open
proxy, pas à l'oracle exact ; lots/ticks/marge/frais sont des hypothèses
Hyperliquid de référence, pas des paramètres historiques Binance vérifiés.
Les montants USDT sont assimilés au dollar pour ce transfert, sans modéliser
USDT/USDC. Ces limites empêchent une promotion réelle même en cas de réussite.

## Livraison et reproduction

90 simulations publiées :3 panneaux×3 règles×5 scénarios×2 sensibilités
d'infrastructure.98 artefacts reproduits à l'identique, dont l'incertitude
passive ; vingt anciens scénarios natifs complets économiquement identiques.
Neuf tests supplémentaires, suite complète **298 tests**, lint/format288
fichiers et mypy70 sources passent. Les acquisitions et calculs sont terminés.
Aucun achat, ordre réel, service ou serveur modifié. Recherche toujours active.
