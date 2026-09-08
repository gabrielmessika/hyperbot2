# Diagnostic du capital et du drawdown, sans promotion statistique

Ce diagnostic est décidé après les résultats positifs du panier acheteur
sur trois panneaux et l'échec de son filtre statistique. Cet échec reste
acquis ; le diagnostic n'abaisse pas ce filtre et ne peut pas autoriser un GO.
Il répond à la question économique : que conserve un compte1 000 $ sous
contraintes natives et avec un arrêt20/30 %, plutôt qu'un notionnel théorique ?

Signaux et sélection identiques aux artefactsv2 de volatility_long_2024 :
onze actifs, volatilité30 jours, lundi00h, trois faibles/trois fortes toutes
achetées, notionnels cibles égaux, garde168h. Recalculer les sélections et
les comparer intégralement aux artefacts précédents avant simulation.
Contrôle : achat hebdomadaire des onze actifs, mêmes dates/horizon.

Réutiliser sans modification le moteur native_portfolio et ses lots/ticks,
minimum10 $, reports d'ordres trop petits, comptes natifs, frais sur ordres
effectifs et funding sur inventaire détenu. Une seule poche, budget100 %,
aucun prêt d'argent entre comptes, aucune position courte intentionnelle.
Les positions et écarts non exécutés ne sont pas supprimés du bilan.

Matrice fixe :3 panneaux indépendants (Binance2024 corrigé explicitement,
Binance2025, Hyperliquid2026),2 règles, caps bruts à l'entrée0,5/1,5x,
arrêts20/30 %,5 scénarios de coût, infrastructure0/20 $ par30 jours.
Soit240 simulations. Capital initial1 000 $ pour chaque simulation ; ce ne
sont pas trois années de gains chaînées ou des reprises après arrêt.

Frais/slippage centraux4,5/2bps par transaction ; stress9/5 ; retard entrée
et sortie1h ; funding adverse ; zéro coût descriptif. L'infrastructure20 $
est une sensibilité hypothétique, pas une facture réelle, et continue après
un arrêt. Aucune collecte, dépense ou exécution réelle.

Le drawdown comprend le PnL ouvert et tous les coûts depuis le sommet de
l'equity. Arrêt irréversible dès franchissement observé ; aucun redémarrage,
clipping, rattrapage ou hausse automatique du levier. Conserver dépassements,
enveloppe prudente OHLC, heures sous sommet et toute poussière terminale.
Le cap est un budget d'entrée ; sa dérive après mouvement doit être publiée.

Publier gains nets, équivalent mensuel géométrique sur toute la durée du
panneau (warmup et immobilisation inclus), mois rouges, frais/funding/infra,
drawdown observé/enveloppe, arrêts, marge et positions terminales. Pour chaque
cap/limite/infra, indiquer si les quatre scénarios payants sont positifs,
enveloppe sous la limite, marge sans incident et bilan terminal plat dans
les trois panneaux. Ce résultat est un diagnostic historique de faisabilité,
pas la validation d'une espérance future ou du filtre statistique précédent.

Les dates restent celles des études événementielles : premières positions
5 février2024,3 février2025,23 mars2026. En particulier, le choc du19 janvier2025
n'est pas exposé dans ce diagnostic. Un éventuel candidat devrait encore
être testé sur une chronologie sans remise à zéro annuelle du warmup/capital.
Ne pas masquer cette limite par un titre de rendement annuel complet.

Les historiques Binance, le dollar assimilé àUSDT, la marge simplifiée,
les paramètres Hyperliquid de référence et les proxies open+60s restent
des limites. Aucune qualification d'exécution native sur Binance n'est déduite.
Conserver résultats négatifs, contrôles et protocoles, sans réglage après PnL.
