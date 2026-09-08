# Portefeuille funding : protocole avant résultats de sizing

Étude de recherche, sans ordre, serveur modifié ni dépense. Les rendements
d'événements 72 h ont déjà été consultés ; aucune prétention de holdout.

## Données et signal

Réunir les archives natives des 19 altcoins, **16 juillet–6 septembre exclusif,
52 jours**, sans trou ni remise à zéro au 7 août. Signal identique : moyenne
funding sur huit heures anciennes >=0,5 bp/h absolu, quatre heures suivantes
réduites de moitié, ratio entre −0,25 et 0,5 ; première apparition seulement,
73 h entre candidats d'un actif. Sens du funding ancien, détention **72 h**.
Les signaux sont indépendants des remplissages, du sizing et des coûts.

Entrée/sortie hypothétiques à open+60 s, prix open ; retard supplémentaire
une heure en stress. Timestamps de funding contrôlés avant l'instant d'exécution,
paiements aux seules positions déjà détenues, valorisés à l'open comme proxy
de l'oracle. Minimum douze heures de passé. Refuser les nouvelles entrées dont
la sortie différée manquerait de prix dans la fenêtre. Sortie terminale des
comparateurs au dernier open+60 s ; dernière heure ensuite en cash.

## Capital et allocation

Capital initial **1 000 $**, equity composée avec positions ouvertes. Trois
plafonds de notional brut **à l'entrée : 0,5x /1x /1,5x**. Un actif reçoit au
plus un tiers du plafond total ; les candidats simultanés partagent également
le budget encore disponible, sans classement selon leurs gains historiques.
Tenir compte des coûts immédiats dans le plafond. Quantités natives arrondies
vers le bas, minimum 10 $ par ordre ; aucune redistribution des petits reliquats.
Pas de rééquilibrage fictif des positions existantes : leur exposition peut
dériver avec les prix. Publier l'exposition effective maximale.

Hypothèse de marge cross sur les perpétuels core avec levier de configuration
constant 2 ; vérifier absence de restriction isolated dans le snapshot et
maxLeverage >=3. Maintenance stress uniforme 20 % du notional, plus prudente
que le premier palier de ces actifs ; pas de liquidation native reconstituée.
Les métadonnées courantes ne prouvent pas leur historique ni les marks natifs.

Pas de stop individuel ajouté au signal événementiel. Arrêt définitif du compte
lorsque le drawdown observé atteint 20 % depuis son sommet ; décision à la clôture
horaire, liquidation simulée au prochain open+60 s. Un gap observé à l'open peut
aussi déclencher cette sortie. Conserver pertes et dépassements, pas de reprise,
pas de martingale ou d'augmentation du levier après pertes.

## Scénarios et comparateurs

Taker central 4,5 bps/côté et slippage 2 ; stress coûts 9/5 ; retard une heure ;
funding adverse en débit absolu ; contrôle sans aucun coût de trading. Coût
d'infrastructure marginal 0 et sensibilité 20 $/30 jours, débités chaque heure.
Ces budgets sont hypothétiques, aucune dépense engagée.

Trois comparateurs long : panier des 19 actifs conservé jusqu'à la fin ; panier
des 19 avec entrées périodiques toutes les 73 h et sortie 72 h ; CASHCAT seul
conservé avec le même plafond par actif (un tiers du total). Entrées initiales
à la douzième heure, règles de coûts/arrondis/marge/drawdown identiques. CASHCAT
est un diagnostic de concentration choisi après l'étude, pas un nouvel univers
de stratégie validé. Ne pas choisir le meilleur comparateur pour le promouvoir.

## Mesure et décision

Courbe horaire, cash, latent, funding, coûts, PnL et dates de chaque cycle.
Drawdown incluant opens, clôtures et coûts ; enveloppe adverse OHLC indépendante
des actifs, incluant positions avant/après transactions. Cette enveloppe peut
surévaluer le risque, mais les seules sorties ne le prouvent pas. Publier
mois/périodes positifs et négatifs, pire perte, temps sous le sommet, récupération,
contribution CASHCAT, respect du stress de marge et frais d'infrastructure.

Poursuivre une taille si les quatre scénarios payants restent globalement
positifs et sous 20 % dans l'enveloppe de risque, sans violation de marge. Aucun
mois rouge n'est un veto isolé. Comparer rendement net cumulé et équivalent
mensuel géométrique à la cible 15–20 %, sans en faire une prévision ni garantie.
Même en cas de passage, 52 jours et un univers choisi a posteriori ne suffisent
pas à un GO : qualification d'exécution et autre historique gratuit nécessaires.

Enregistrer code, configuration/protocole, sources/checksums, scénarios et
reproduction offline. Les anciens résultats restent inchangés.
