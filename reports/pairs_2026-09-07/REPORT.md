# Investigation BTC/ETH — 7 septembre 2026

**Hypothèse exploitable non confirmée dans la définition testée.** Les écarts
BTC/ETH se réduisent souvent, mais leur réduction ne fournit pas ici une
espérance positive démontrée après les coûts. Ne pas développer ou lancer
un bot de trading sur cette règle ; aucun GO de validation nouvelle ou de live.

L’étude est exploratoire : les données avaient déjà été consultées pour
d’autres stratégies. Le [protocole](PROTOCOL.md), son
[enregistrement](registration.json) et le [code figé avant calcul](code_lock.json)
sont conservés. Aucun réglage de stratégie après lecture des résultats.

## Hypothèse et données

Réutilisation des 4 320 bougies horaires et 4 320 taux de funding par actif
déjà collectés, du 10 mars au 6 septembre 2026 00:00 UTC exclu. Les 30 premiers
jours constituent la chauffe ; l’étude couvre ensuite cinq blocs de 30 jours,
du 9 avril au 6 septembre. Le lecteur existant vérifie les checksums,
l’alignement horaire, OHLC, trous et doublons. Une seule nouvelle requête
publique vérifie le pas des quantités : BTC 5 décimales, ETH 4.

Le modèle ajuste les logarithmes des prix ETH et BTC sur les 720 clôtures
précédentes, sans utiliser la clôture du signal. Signal pour un écart compris
entre 2 et 4 écarts-types ; achat de l’actif relativement en retard et vente
de l’autre, quantités ajustées par le bêta estimé. Le modèle et les quantités
sont ensuite gelés : aucun recentrage de la moyenne ne peut créer une
convergence artificielle pendant la position.

3 575 modèles horaires calculés ; **33 événements espacés d’au moins 25 h**.
Le résultat principal est le rendement à **6 h**, fixé avant calcul. Les
horizons 1 h et 24 h sont des comparaisons préenregistrées.

## Résultat du test principal

Rendements exprimés en points de base du **notionnel brut total des deux
jambes** ; 1 bp = 0,01 %. Entrée à l’ouverture horaire suivante, observation
à une ouverture future. Le modèle est gelé et la réduction de l’écart est
mesurée depuis l’entrée, sans créditer un mouvement antérieur à l’entrée.

| Horizon | Écart absolu réduit | Rendement moyen brut | Après frais/slippage, avant funding | Intervalle bootstrap 95 % du net |
|---|---:|---:|---:|---:|
| 1 h | 51,5 % | −4,82 bps | −17,83 bps | [−31,81 ; −8,54] bps |
| **6 h, principal** | **60,6 %** | **−5,47 bps** | **−18,48 bps** | **[−56,60 ; +4,15] bps** |
| 24 h | 63,6 % | −6,82 bps | −19,82 bps | [−51,52 ; +3,50] bps |

Le taux de réduction du spread n’est pas le taux de trades rentables : à 6 h,
16 événements sur 33 sont positifs après frais/slippage, soit 48,5 %.
Le gain net moyen des événements gagnants est +20,94 bps ; la perte nette
moyenne des autres est −55,59 bps. Les pertes plus importantes absorbent les
petits retours de l’écart.

Un événement extrême atteint −556,63 bps dans cette étude à horizon fixe,
qui n’applique pas de stop. Vérification descriptive après résultat, sans
changer la décision : même en le retirant, la moyenne nette à 6 h reste
−1,67 bps sur les 32 autres événements. Le scénario économique ci-dessous
dispose, lui, de sorties de risque horaires.

Le bootstrap rééchantillonne 5 000 fois des blocs mobiles de sept jours,
y compris les jours sans événement, avec le seed préenregistré. Il traite
conjointement somme des rendements et nombre d’événements. L’intervalle
principal inclut zéro : **l’étude ne démontre pas une espérance négative
universelle, mais elle ne confirme pas l’avantage positif recherché**.
Avec seulement 33 événements, l’incertitude reste importante.

## Pourquoi la corrélation ne suffit pas

La corrélation médiane des rendements horaires dans les fenêtres d’ajustement
est élevée : 0,889. Le bêta de prix est toutefois variable : environ 0,076 à
2,024, médiane 1,191. Les coefficients ne représentent pas une relation
fondamentale immuable entre les deux actifs.

La demi-vie descriptive médiane des résidus ajustés est d’environ **47 h**,
contre un horizon principal de six heures. Cette statistique utilise les
résidus d’ajustement ; elle ne constitue ni un test de cointégration ni une
prévision fiable de convergence. Dans la simulation, une seule position
atteint le seuil de convergence, 29 sortent à 24 h et trois sur règle de risque.

## Simulation économique sur 1 000 $

Une seule règle, 50 $ maximum par jambe, taille éventuellement réduite par
le risque de spread, minimum de 10 $ par jambe après arrondi. Le plus grand
notionnel brut réellement simulé est 97,38 $. Aucun levier ni taille augmenté
pour atteindre la cible de rendement.

Sortie à la prochaine ouverture après convergence, franchissement de la
limite de spread ou de perte marquée ; sinon sortie à 24 h. Les deux jambes
sont supposées exécutables au prix simulé, sans preuve historique de carnet.
Les limites de perte ne sont pas garanties par ces données horaires.

| Bloc de 30 jours | Cycles | PnL trading net, scénario de base | Après 20 $ d’infrastructure |
|---|---:|---:|---:|
| 9 avril–9 mai | 7 | −0,04 $ | −20,04 $ |
| 9 mai–8 juin | 9 | −2,52 $ | −22,52 $ |
| 8 juin–8 juillet | 5 | −1,26 $ | −21,26 $ |
| 8 juillet–7 août | 8 | +0,39 $ | −19,61 $ |
| 7 août–6 septembre | 4 | −0,19 $ | −20,19 $ |
| **Total** | **33** | **−3,62 $** | **−103,62 $** |

Les blocs réinitialisent leur capital et ferment leurs positions à la
frontière. Leur somme n’est pas une courbe de capital composé. Le total
après infrastructure représente environ −10,36 % des 1 000 $ de référence
sur cinq blocs ; ce n’est pas une perte mensuelle de 10,36 %.

| Scénario | Trading avant infrastructure | Après infrastructure |
|---|---:|---:|
| Base : frais 4,5 bps + slippage 2 bps par exécution | −3,62 $ | −103,62 $ |
| Stress : 9 + 5 bps | −7,79 $ | −107,79 $ |
| Entrées retardées d’une heure supplémentaire | −0,66 $ | −100,66 $ |
| Zéro frais, slippage et funding | +0,62 $ | −99,38 $ |

Le profit factor des cycles nets de base est **0,58**, sous 1,20. Les coûts
fixes dominent le résultat total, mais le trading est déjà négatif avant
infrastructure. Augmenter le capital n’est donc pas justifié par cette preuve.

Frais simulés de base : 2,50 $ sur l’ensemble des cycles ; funding adverse
0,61 $. Le contrôle de funding signé aurait coûté environ 0,06 $ : remplacer
l’hypothèse adverse par ce proxy signé laisserait le trading à environ
−3,07 $, à trajectoires identiques. Ce n’est pas une nouvelle variante optimisée.

Le barème de base des perps et le paiement horaire du funding sont documentés
par Hyperliquid : [frais](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees),
[funding](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding).
Le scénario adverse débite les deux jambes sans crédit. L’oracle historique
du funding manque : le prix d’ouverture sert de proxy, pas de décompte exact.
Le pas de quantité vient des métadonnées actuelles, sans preuve de stabilité
sur tout l’historique. Ni frais spécifiques au compte, ni fills réels validés.

## Décision et livraison

Un seul des cinq critères de poursuite passe : le minimum de 30 événements.
La borne inférieure positive du test principal, le PnL de base positif après
infrastructure, quatre blocs positifs et le PF >1,20 échouent.
**Statut : `HYPOTHESIS_NOT_CONFIRMED`.** Cette règle n’est pas candidate à
une validation prospective. La conclusion ne couvre pas toutes les stratégies
de paires ou tous les horizons, mais changer leurs paramètres sur ces mêmes
résultats serait une nouvelle recherche, pas une validation indépendante.

Code livré : `research/pairs.py`, `scripts/investigate_pairs.py`, quatre tests
supplémentaires. Réutilisation du lecteur d’archives, des contrôles de qualité
et de provenance. **178 tests passent**, lint/format et mypy sur 46 modules.
Les tests vérifient notamment l’absence de fuite future, le modèle gelé,
la neutralisation d’un mouvement commun dans un exemple contrôlé et les
quatre exécutions/funding dans la comptabilité de la paire.

Aucun accès à une clé, aucune modification du serveur, aucun ordre ou service
lancé. Les anciennes pistes maker restent suspendues. Les détails, features
et cycles restent sous `data/pairs_2026-09-07/run-001/`, hors Git ; le
[résumé complet](summary.json) et le [manifeste](evidence_manifest.json)
identifient les sources et versions.

Reproduction depuis les raws existants, dans un nouveau répertoire :

```bash
uv run python scripts/investigate_pairs.py \
  --history data/search_2026-09-06/history \
  --metadata data/pairs_2026-09-07/metadata.json \
  --output data/pairs-recheck
```

La commande effectue les calculs offline sans requête, refuse un répertoire
existant et conserve les résultats défavorables. Aucun résultat de cette
étude ne valide +30 % par mois.
