# Recherche de pistes — protocole enregistré avant les nouveaux calculs

Date : 6 septembre 2026. Demande : poursuivre jusqu’à un GO, explorer les
alternatives si une piste échoue. Les résultats défavorables seront conservés.
Un GO économique ne sera pas remplacé par un GO de fonctionnement logiciel.
Les gates existantes, le capital de 1 000 $ et l’interdiction du live restent
inchangés. Cette extension autorise de nouvelles hypothèses de recherche, sans
reprendre les stratégies directionnelles de TRIDENT/BOT05.

## Branches et décisions

1. L4 maker HIP-4 : chercher un accès déjà configuré et des alternatives à
   QuickNode. Comparer schéma, historique, prix et accès réel. Sans accès, ne
   pas inventer une qualification ; poursuivre les autres branches.
2. Arbitrage structurel outcomes : lire les métadonnées et carnets publics des
   groupes multi-outcomes. Tester le coût visible du panier complet de YES et
   les violations de monotonie des binaires partageant référence et échéance.
   Zéro frais fournit un plafond exploratoire ; toute anomalie nécessite ensuite
   une preuve causale de profondeur, frais, settlement et exécution des jambes.
3. Portage spot/perp : BTC, ETH, SOL, HYPE fixés avant les mesures. Historique
   funding sur 180 jours clos au 6 septembre 2026 00:00 UTC. Publier les six
   blocs consécutifs de 30 jours, sans extrapoler le dernier taux horaire.
   Benchmark favorable : notionnel short 500 $ + achat spot 500 $, capital
   1 000 $, sans coûts ni basis. Un rendement insuffisant dans cette hypothèse
   ne justifie pas une recherche coûteuse pour la cible +30 %.
4. Taker horaire : deux hypothèses simples nouvelles, sans optimisation :
   breakout Donchian 24 h et retour à moyenne 24 h à deux écarts-types.
   Même univers BTC/ETH/SOL/HYPE, OHLCV Hyperliquid 1 h sur les 180 jours.
   Les 60 premiers jours servent au développement, les 30 suivants au contrôle,
   les trois derniers blocs de 30 jours sont réservés à l’évaluation finale.
   Les frontières forcent une liquidation : aucune position ne traverse un fold.

## Simulations taker exploratoires

Signal à la clôture de la bougie, exécution au plus tôt à l’ouverture suivante.
Breakout : clôture au-dessus du plus haut des 24 bougies précédentes → achat ;
en-dessous du plus bas → vente. Retour à moyenne : clôture au-dessous/au-dessus
de la moyenne ±2 écarts-types des 24 clôtures précédentes → achat/vente.
Stop fixe à 2 ATR des 24 dernières bougies closes, horizon maximal 24 h, un
seul trade par coin. Pas de prise de profit ni de recherche de paramètres.
Notionnel ≤50 $/coin, quatre coins maximum, risque au stop ≤2,50 $/coin,
réduction de taille de moitié après 8 % de drawdown mensuel ; blocage du jour
à −15 $ et arrêt dur à −120 $ depuis le pic. Ces contrôles simulés ne garantissent
pas de limite réalisée en cas de gap. Les sorties au stop prennent le pire du
stop et de l’ouverture en cas de gap ; aucun chemin intrabougie inventé.

Frais hypothétiques conservateurs : 4,5 bps par côté, slippage 2 bps par côté.
Stress : frais doublés, slippage 5 bps/côté ; latence stress : entrée décalée
d’une bougie supplémentaire. Funding : coût adverse absolu au taux historique,
sans crédit favorable ; publier aussi le scénario zéro coûts comme contrôle
favorable. Infrastructure : 20 $/30 jours. Aucun levier ni taille rehaussé pour
atteindre la cible. Pas de fill maker. Les OHLC et coûts hypothétiques ne peuvent
pas devenir une preuve d’exécution A.

## Critères et ressources

Publier toutes les branches/variantes, cycles, frais, funding, rendement par
fold et distribution des blocs de 30 jours. Le contrôle favorable peut rejeter
une variante économiquement insuffisante ; un résultat favorable autorise
seulement une investigation sur données d’exécution qualifiées. Un GO économique
reste soumis à l’ensemble des gates applicables, aux 14 jours shadow et aux
preuves hors échantillon ; aucune autorisation d’ordre n’est implicite.

Au plus 100 requêtes publiques, 50 Mo téléchargés et 30 minutes CPU pour cette
vague. Requêtes séquentielles ou à concurrence faible, pagination vérifiée,
artefacts avec hashes, périodes manquantes explicites. Aucun service permanent,
abonnement, création de compte ou message à un tiers. Si une source refuse
l’accès, enregistrer ce résultat et utiliser les données autorisées disponibles.
