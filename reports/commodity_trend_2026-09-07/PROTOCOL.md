# Tendance métaux/énergie : collecte et test fixés avant résultats

Univers fixé d'après les instruments et frais, sans consulter leurs rendements
historiques : `xyz:GOLD`, `xyz:SILVER`, `xyz:CL`. L'or apporte un métal à frais
standards, l'argent et le pétrole WTI deux marchés growth. Ne pas supposer que
tous les marchés HIP-3 bénéficient du tarif réduit. Exclure Brent pour ne pas
doubler arbitrairement l'exposition pétrole.

## Collecte gratuite bornée

Réutiliser le client public natif sans credentials : 40 requêtes maximum,
50 Mo maximum, destination neuve append-only avec checksums. Bougies 1 h et
funding du 12 février au 6 septembre 2026 exclusif (206 jours), au plus dix
pages funding par instrument. Vérifier identités, continuité, volumes et OHLC.
Si couverture différente, publier la qualité avant calcul et figer explicitement
l'intersection ; aucune imputation de prix ou funding. La limite native des
5 000 bougies horaires ne prouve pas une couverture de douze mois.

## Règle de portefeuille

Un seul modèle de tendance, aucun balayage de paramètres. Entrée long à l'open
suivant une close au-dessus des plus hauts des 240 heures précédentes (bougie
signal exclue du canal), short symétrique. ATR moyen des 24 true ranges complets.
Signal et ATR uniquement sur bougies complètes. Stop initial à trois ATR du
prix d'entrée ; trailing stop à trois ATR de la dernière close, mis à jour pour
la bougie suivante seulement. Sortie après sept jours maximum ; délai minimal
de 24 heures avant réentrée sur le même actif après toute sortie.

Capital initial 1 000 $, PnL réinvesti normalement, aucune hausse après perte.
Risque initial visé 1 % de l'equity par position au stop théorique, plafonné
par le notional. Trois scénarios de taille **enregistrés ensemble** : notional
maximal par actif de 1/6, 1/3 et 1/2 de l'equity, donc au plus 0,5x, 1x et 1,5x
brut à l'ouverture des trois positions. Ne pas augmenter les positions ouvertes.
Arrondir les quantités vers le bas selon le snapshot natif ; minimum 10 $.
Faire respecter aussi le plafond global sur la valorisation à l'open avant
chaque entrée, sans compter le capital trois fois. Pas de short d'actions
externes, aucun compte ou client de signature.

Arrêt définitif du scénario à 20 % de drawdown depuis le sommet observé,
avec liquidation simulée au prochain open après observation de la perte.
L'arrêt peut dépasser 20 % en cas de gap : publier le dépassement, sans
tronquer artificiellement les pertes au seuil. Le critère utilisateur porte
sur le drawdown constaté, pas sur le nom du stop. Après arrêt, pas de reprise
ni de remise à 1 000 $. Les simulations sont distinctes du superviseur live.

## Coûts et risques mesurés

Frais du snapshot natif : GOLD 9 bps, SILVER/CL 0,9 bp par côté. Tarif actuel
comme sensibilité, historique complet non présumé. Slippage central 2 bps/côté ;
stress frais doublés et slippage 5 bps/côté ; retard d'une heure du signal avec
prix d'entrée ultérieur, sans accès à la bougie en cours. Funding signé réel
à l'open de chaque heure pour les positions déjà détenues ; stress séparé en
valeur absolue. Prix de funding = open proxy, pas mark historique garanti.
Publier également contrôle sans coûts. Les scénarios sont alternatifs.

Stop traversé par une bougie : prix le plus adverse entre open et stop, puis
slippage. En cas de gap, prendre l'open adverse, pas le stop fictif. Volumes
nuls ou trous : pas d'entrée ; un trou de série empêche l'évaluation. Une
bougie ne qualifie pas la profondeur, les sauts intra-bougie ni un fill réel.

Enregistrer equity horaire, PnL latent et réalisé, frais, funding, notional,
drawdown, mois gagnants/perdants, gains/pertes mensuels, temps sous le sommet,
rendement total et équivalent mensuel composé. Les mois rouges sont acceptés
si l'ensemble est largement positif et drawdown <=20 %. Courbe à coût marginal
d'infrastructure nul et sensibilité 20 $/30 jours, débitée au fil du temps.
Les douze mois ne peuvent pas être validés par six/sept mois de données.

Cette première passe doit établir l'économie et la qualité du risque mesurable,
pas accorder un GO live. Si un candidat est positif après stress de coûts et
funding, drawdown <=20 %, comparer sa stabilité sur périodes ultérieures et
autres historiques sans exiger chaque mois positif. Aucune sélection du meilleur
actif, stop ou délai après résultat. Une forte performance brute sans robustesse
ou sans marge suffisante aux coûts ne justifie pas une hausse de levier.
