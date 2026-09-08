# Exécution native causale du portefeuille partagé

Étude enregistrée avant calcul. Garder le panel gratuit 18 actifs /204 jours,
les signaux cassure sans compression et rotation hebdomadaire, les horizons
24/168 heures, les budgets 50/50 et le cap brut à l'entrée 1,5x. Comparer
seuils de drawdown 20/30 %, cinq scénarios déjà définis et sensibilités
d'infrastructure 0/20 $ par 30 jours. Aucun réglage choisi sur le résultat.

Remplacer le compte virtuel comme source de capital par un seul compte natif.
Les intentions par mécanisme restent des lots à horizon fixe ; elles se
compensent en une cible signée par actif. L'allocation utilise l'equity du
compte réellement simulé, le brut des intentions actives et une réserve pour
les résidus entre positions natives et anciennes cibles. Le budget inactif
n'est pas prêté à l'autre mécanisme. Réutiliser la formule de budgets séparés.

Chaque heure : marquer les anciennes positions à l'open, déduire infra et
funding réellement dus avant open+60 secondes, observer drawdown et marge,
expirer les intentions à leur horizon, allouer les signaux admissibles puis
calculer les deltas nets. Pour dimensionner avant leur exécution, réserver
prudemment frais/slippage des intentions expirées et de l'ancien résidu.
Cette réserve sert seulement au dimensionnement ; seuls les coûts réellement
simulés sont débités. Les fills restent au proxy open+slippage, à open+60 s.

Arrondir chaque prix de fill supposé au tick perp natif dans le sens adverse
(cinq chiffres significatifs au plus, au plus 6-szDecimals décimales,
prix entiers toujours admis). Quantités aux lots natifs, minimum de 10 $
pour tous les ordres sans exception reduce-only présumée. Aucun fill de
montant insuffisant, aucun arrondi de quantité vers le haut pour forcer un fill.

Traiter les réductions sans inversion avant les autres deltas, puis ordre
lexical stable. Refuser/reporter une augmentation ou inversion si elle
dépasse le cap de brut natif après frais/slippage ou la marge initiale 2x.
Les changements purement réducteurs restent autorisés lorsque réalisables.
Réessayer le delta entre position détenue et cible à chaque heure : il peut
devenir réalisable, être remplacé par une nouvelle cible ou disparaître.
Un ordre non exécuté ne modifie jamais la position détenue ni son cash.

Le funding porte sur la position native détenue, pas sur les intentions ;
en scénario adverse, il est débité en valeur absolue sur ce notionnel net.
Comptabiliser prix moyen, PnL réalisé, frais et funding par épisode natif
(de position nulle jusqu'à position nulle ou inversion). Inclure toute
position résiduelle terminale à sa valeur marquée, sans clôture fictive.
Présence d'un résidu terminal ou incident de marge : qualification suspendue.

Arrêt global irréversible sur drawdown observé, sans reprise ni troncature
des dépassements. Un déclenchement à la clôture horaire ferme au prochain
open réalisable. Les résidus continuent de porter risque et funding après
arrêt. Mesurer aussi une enveloppe OHLC prudente sur les positions natives
avant/après transaction et toutes les phases de cash ; ne pas confondre
ce majorant avec un chemin intrahoraire observé. Conserver le modèle virtuel
original en comparaison, sans exiger des gains identiques après correction.

Le filtre exploratoire exige les quatre scénarios payants positifs, sans
incident de marge, avec enveloppe <= seuil et aucune position terminale.
Il ne vaut pas GO : données de prix/fills/oracle approximatives, historique
déjà exploré et absence de validation indépendante restent explicités.
Publier tous les cas, contrôles de rapprochement, coûts, résidus et refus.
Pas d'achat, de signature, d'ordre réel ou de modification serveur.
