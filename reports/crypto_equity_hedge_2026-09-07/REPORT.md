# Actions crypto couvertes par BTC : hypothèse non confirmée

**Les deux directions échouent après coûts.** Le retour à la moyenne gagne
seulement 7,78 $ sur 180 jours avant tout coût, puis perd 9,90 $. La
continuation perd 25,68 $ après coûts. Cette règle est suspendue, sans ajuster
les seuils ni sélectionner uniquement l'actif ou le segment gagnant.

## Règle et périmètre

[Protocole enregistré](PROTOCOL.md) avant calcul : régression des rendements
intraday COIN/BTC et MSTR/BTC sur les 20 séances précédentes, avec intercept.
À 14 h New York, détecter un écart d'au moins deux écarts-types résiduels après
couverture BTC ; beta entre 0,25 et 4, corrélation minimale 0,5. Entrer en sens
inverse de l'écart pour le retour à la moyenne, dans son sens pour le contrôle
continuation. Sortie le lendemain à 14 h, jours ouvrés seulement, sans week-end
ni entrée avant jour férié. Un seul panier sélectionné par date.

Les historiques natifs existants couvrent l'intersection du 10 mars au
6 septembre 2026, soit 180 jours, warm-up inclus dans le dénominateur.
125 séances /250 observations action : 40 en warm-up ou invalides, 16 modèles
rejetés, 179 sans signal et 15 signaux action. Deux dates ont deux signaux :
la règle du plus grand écart retient **13 paniers**, trois COIN et dix MSTR.

Le lien économique à BTC motive le test, sans garantir de convergence :
[Strategy décrit une exposition amplifiée à BTC](https://www.strategy.com/learn),
mais son action n'est pas interchangeable avec BTC. La relation est estimée
sur les données antérieures, pas supposée constante ni utilisée comme arbitrage
sans risque.

## Résultats après les coûts des deux jambes

Chaque scénario utilise 1 000 $ de notional **total**, partagé selon beta entre
l'action et BTC, jamais 1 000 $ par jambe. Les deux directions sont des
simulations alternatives, non cumulables. Quantités fractionnaires constantes,
prix open horaires, funding signé et slippage explicite. Tous les 13 signaux
ont des volumes action non nuls à l'entrée/sortie centrales et retardées ;
ce critère ne démontre pas la profondeur ni l'exécution réelle.

Frais par côté : COIN 0,9 bp, MSTR 9 bps, BTC 4,5 bps. Le barème action est
recalculé depuis le snapshot natif avec le module de frais déjà audité et
comparé au protocole. La [documentation trade.xyz](https://docs.trade.xyz/trading/fees)
étaye la différence growth/standard. L'historique exhaustif des changements
de barème reste inconnu : sensibilité au tarif observé, pas facture historique.

| Scénario | Retour à la moyenne, bps/panier | PnL proxy 180 j | Continuation, bps/panier | PnL proxy 180 j |
|---|---:|---:|---:|---:|
| Sans frais, slippage ni funding | +5,99 | +7,78 $ | −5,99 | −7,78 $ |
| Central | −7,62 | −9,90 $ | −19,75 | −25,68 $ |
| Frais/slippage renforcés | −23,30 | −30,29 $ | −35,43 | −46,06 $ |
| Entrée/sortie retardées d'une heure | −13,99 | −18,18 $ | −13,37 | −17,38 $ |
| Funding toujours défavorable | −9,83 | −12,77 $ | −21,80 | −28,33 $ |

Le proxy central /30 jours après 20 $ d'infrastructure hypothétique vaut
−21,65 $ pour le retour à la moyenne, −24,28 $ pour la continuation. Aucune
dépense réelle engagée. Ces valeurs ne permettent pas de viser les 150–200 $
mensuels acceptés par l'utilisateur.

## Stabilité et risque

Avant le 1er juillet : neuf paniers, retour à la moyenne −38,48 $,
continuation +13,82 $. Depuis le 1er juillet : quatre paniers, respectivement
+28,58 $ et −39,49 $. Le signe change entre segments. Les quatre trades
récents gagnants de la première direction sont trop peu nombreux pour valider
un edge ; les vingt dates minimales par segment ne sont atteintes nulle part.

Les IC bootstrap 97,5 % de moyenne par blocs de trois semaines sont
**[−140,72 ; +67,23] bps** pour le retour à la moyenne et
**[−93,00 ; +111,53] bps** pour la continuation. Les IC du segment récent sont
non qualifiés car trop de tirages n'ont aucun événement. Les historiques ont
déjà été consultés pour d'autres hypothèses : le découpage chronologique ne
constitue pas une réserve globalement vierge.

Le retour à la moyenne sur COIN est positif (+18,92 $) mais seulement sur trois
trades ; MSTR perd 28,83 $. Ne pas supprimer MSTR après coup pour présenter une
stratégie COIN validée. Tous les gates enregistrés échouent pour les deux sens.

Les drawdowns calculés aux sorties atteignent 54,90 $ et 68,84 $ dans le scénario
central ; ce ne sont pas des drawdowns intraday. Le pire trade de retour à la
moyenne perd 36,05 $, supérieur à la limite journalière fondation de 15 $ pour
1 000 $. Ce proxy sans stops, contraintes de taille ni liquidation ne valide
donc pas le superviseur de risque. Il sert ici à rejeter une économie déjà
négative ; aucune augmentation de taille ou de levier n'est proposée.

## Reproduction et livraison

Module immuable `return_hedge`, script offline et tests : estimation de beta
avec résidus non nuls, cas dégénéré, partage du notional et signes du funding
des deux jambes. Le loader natif, le calendrier, le barème et `leg_return`
proviennent d'Hyperbot2 existant ; aucun import runtime des anciens bots.

233 tests passent ; après clarification des accumulateurs Decimal pour mypy,
les deux tests ciblés passent de nouveau. Lint/format 196 fichiers et mypy
59 sources passent. Les corrections de type et le raccordement au barème natif
ne changent pas les décisions ni les PnL du premier calcul. Quatre artefacts
finaux reproduits exactement : [preuve](reproduction.json). Raw et baselines
antérieures conservés. Aucun serveur, service, wallet ou ordre modifié.

État des deux règles : `HYPOTHESIS_NOT_CONFIRMED`. Recherche globale active.
Le prochain lot doit changer de moteur de rendement, sans optimiser cette
régression sur ces treize résultats. Une piste disponible gratuitement reste
la tendance sur les marchés HIP-3 non crypto à frais réduits (métaux/énergie) :
qualifier leur historique natif avant tout test et figer un protocole distinct.
