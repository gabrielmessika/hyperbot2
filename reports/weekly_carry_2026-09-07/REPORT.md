# Carry relatif hebdomadaire : revenus insuffisants après prix et frais

**`WEEKLY_CARRY_CROSS_PERIOD_SCREEN_FAILED` : aucun candidat retenu.**
Le panier reçoit effectivement du funding, mais les mouvements de prix et
les frais absorbent ce revenu dans les deux panneaux. Inverser les côtés
ne produit pas non plus un résultat net robuste. Le diagnostic s'arrête
avant une simulation de capital ; aucun rendement mensuel ou drawdown de
compte n'est déduit de ces événements.

## Règle fixée avant calcul

[Protocole](PROTOCOL.md), [enregistrement actif](registration_v2.json).
Le premier enregistrement est conservé ; la seconde version corrige uniquement
le format d'une ligne et le chemin d'enregistrement du script, avant tout PnL.
Aucune modification économique entre les deux versions.

Onze actifs prédéfinis : ARB, BNB, DOGE, INJ, LINK, NEAR, UNI, WLD, XMR, XRP,
ZEC. Chaque lundi, acheter les trois sommes de funding les plus faibles sur
les 168 heures révolues et vendre les trois plus élevées. Six notionnels
égaux ; détenir une semaine. Entrer uniquement si la recette attendue sous
persistance dépasse 13 bps du notionnel brut, correspondant aux coûts centraux
aller-retour. Exclure le règlement de l'heure du signal et les égalités aux
frontières de sélection. Contrôle : mêmes dates et actifs, côtés inversés.

Cette extension du carry relatif n'efface pas l'échec antérieur sur quatre
grandes cryptos : elle change explicitement l'univers, l'horizon et ajoute
un seuil de couverture des coûts. Aucun de ces paramètres n'est optimisé
après observation des résultats.

Binance 2024–2025 continu : 103 dates examinées, 42 paniers admissibles
(20 datés de 2024 et 22 de 2025), huit abstentions pour égalité. Hyperliquid
2026 : 27 dates examinées, 23 admissibles, aucune égalité. Les autres dates
échouent au seuil économique. La chauffe de sept jours et les sorties
retardées expliquent les bornes calendaires ; aucune remise à zéro annuelle.

## Résultats par panier

Les valeurs suivantes sont des **bps du notionnel brut initial** : 100 bps
valent 1 %. Ce ne sont pas des dollars ni des rendements du capital disponible.

| Panneau | Prix brut | Funding reçu | Frais + slippage | Net central | Net coûts renforcés | Net retard 1 h |
|---|---:|---:|---:|---:|---:|---:|
| Binance 2024–2025 | −18,66 | +20,20 | −13,06 | **−11,51** | −26,58 | −22,19 |
| Hyperliquid 2026 | −29,87 | +17,44 | −13,08 | **−25,50** | −40,59 | −32,10 |

Le funding encaissé est le revenu simulé pendant la détention, pas la
projection utilisée pour entrer. Central : frais 4,5 bps et slippage 2 bps
par côté ; stress 9 et 5 bps. Le funding utilise les règlements datés.

Sur Binance, le central est négatif séparément par année d'entrée : −7,40 bps
en 2024 et −15,25 en 2025. Dix-huit paniers gagnants sur 42, PF 0,93 ; pire
panier −846,26 bps, soit −8,46 % du notionnel brut. Intervalle bootstrap 95 %
de la moyenne [−129,86 ; +106,62] bps.

Sur Hyperliquid, dix paniers gagnants sur 23, PF 0,76 ; pire panier −646,83 bps
(−6,47 % du notionnel). Intervalle [−133,71 ; +78,15] bps. Les vendeurs des
fundings élevés portent la perte agrégée dans les deux panneaux ; aucune
suppression d'actif perdant n'est faite. Les contributions détaillées sont
conservées dans les résumés.

Le contrôle inversé donne −14,60 bps sur Binance et −0,65 sur Hyperliquid,
également négatif sous frais renforcés. Sans frais, slippage ni funding, le
carry donne −18,66 / −29,87 bps. Avec tout funding transformé en débit :
−71,19 / −75,48 bps. Ce dernier scénario mesure la dépendance au financement ;
il ne constituait pas une exigence de rentabilité pour cette hypothèse.
L'échec est déjà présent sous central, coûts et retard avec funding signé.

## Preuves et limites

[Reproduction](reproduction.json) : huit JSON identiques entre les deux
exécutions (qualité, sélections, événements et résumé de chaque panneau).
[Audit indépendant](independent_audit.json) : relecture des sources, calendrier
et sélections calculés à nouveau depuis les paiements passés ; vérification
des 3 900 combinaisons jambe/règle/scénario par un registre cash signé,
sans appeler le calculateur de rendement utilisé par le test. Frais, funding,
agrégats par panier et moyennes concordent. Code de l'audit conservé avec SHA.

331 tests complets passent, dont trois nouveaux tests des signaux couvrant
normalisation des fréquences, causalité, égalités, calendrier, seuil et trous.
Lint et format vérifiés sur 329 fichiers ; typage de 77 sources réussi.
Les qualités des deux panneaux sont identiques aux précédentes après retrait
des seules métadonnées d'exécution inutilisées. Les loaders revalident les
archives et la correction REST explicite ; aucun nouvel appel de données.

Les résultats sont exploratoires : historiques déjà réutilisés, hypothèse
choisie après d'autres essais, univers survivant, transfert de plateforme
Binance USDT et ouvertures horaires utilisées comme fills. La somme nette
des notionnels est nulle à l'entrée ; elle ne couvre ni le bêta ni les écarts
de prix entre actifs.

Sur Hyperliquid, le règlement de funding utilise le prix oracle, comme le
précise la [documentation officielle](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding).
L'ouverture horaire utilisée ici est un proxy, pas une reconstruction exacte
de l'oracle historique. Aucun GO ne pourrait être fondé sur ce seul modèle.
Aucun ordre réel, achat, service ou serveur modifié.

[Verdict](review.json) : les deux panneaux échouent au filtre économique et
à la borne statistique centrale. Ne pas ajouter du levier à cette perte ni
balayer les seuils pour sélectionner rétrospectivement un résultat positif.
Recherche active, plafond de recherche 30 % avec comparaison conservée à 20 %.
