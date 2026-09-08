# Écart actions crypto/BTC : protocole exploratoire

Règle figée avant ses résultats. Les historiques ont déjà servi à d'autres
hypothèses ; le découpage chronologique n'est donc pas une réserve globalement
vierge. Aucun GO live possible sur cette seule exploration.

Hypothèse principale : une variation intraday de COIN ou MSTR anormalement
éloignée de son exposition habituelle à BTC se résorbe le lendemain. Contrôle
enregistré simultanément : continuation du même résidu, avec hedge opposé.
Les relations économiques motivent le test mais ne garantissent pas de
convergence : les actions portent des risques propres à leur société.

## Données et signal

Bougies natives horaires et funding existants, COIN/MSTR via trade.xyz et BTC
sur le DEX natif. Intersection des historiques, du 10 mars au 6 septembre 2026.
Calendrier américain existant, fuseau New York avec DST. Chaque session ouvrée,
calculer le log-return de l'open 10 h à la close de la bougie 13 h (connue à
14 h). Les quatre bougies action doivent avoir un volume strictement positif.
Ne pas utiliser une close ultérieure pour le signal.

Régression OLS avec intercept sur les **20 sessions précédentes**, séparément
pour chaque action : r_action = alpha + beta * r_BTC + epsilon. Écart-type
résiduel estimé avec n−2 degrés de liberté. Pour accepter : beta entre 0,25 et
4 inclus, corrélation >=0,5, sigma résiduel >=0,001. Z du retour de la session
actuelle, calculé avec ce modèle antérieur. Signal si |z| >=2.

Entrée à 14 h New York du lundi au jeudi, sortie le lendemain à 14 h ; les deux
jours doivent être des sessions normales. Pas de trade avant jour férié, pas de
week-end. Si les deux actions signalent, choisir le plus grand |z|, égalité par
nom d'actif. Au plus une paire à la fois, pas de réinvestissement du PnL.
Fade : short action si résidu positif, long sinon ; BTC en sens opposé avec
notional beta fois celui de l'action. Contrôle continuation = directions inverses.

## Exécution et économie

Notional TOTAL maximal 1 000 $ réparti 1/(1+beta) sur action et beta/(1+beta)
sur BTC. Aucune allocation de 1 000 $ par jambe. Prix open horaire suivant les
bougies complètes, quantité fractionnaire constante jusqu'à sortie, pas de
minimum/tick/profondeur simulé : **filtre économique optimiste, pas portefeuille
exécutable ni preuve de capacité**. Rejeter et conserver le signal si le volume
action à l'entrée ou sortie est nul ; compter la couverture d'exécution.

Scénarios :
- central : taker COIN 0,9 bp, MSTR 9 bps, BTC 4,5 bps par côté ; slippage
  action 2 bps, BTC 1 bp par côté, funding horaire signé sur les deux jambes ;
- coûts renforcés : frais doublés, slippage action 5 bps, BTC 3 bps ;
- retard : mêmes signaux et beta, entrée ET sortie retardées d'une heure,
  donc à 15 h en session régulière ; coût central ;
- financement défavorable : coût central, chaque funding est une charge
  absolue sur chaque jambe ;
- sans frais/slippage/funding : contrôle brut.

Le tarif growth de COIN reste une sensibilité au tarif observé, sans timeline
exhaustive historique. Réutiliser `leg_return`, qui compte frais entrée/sortie
et funding avec notional variable à quantité constante. Aucun stop simulé à
un prix garanti à partir de bougies horaires. Signaler drawdown et pire trade
du proxy constant ; les stops/limites de risque fondation restent obligatoires
pour toute promotion et ne sont pas validés ici.

## Critères et limites

Publier ancien (avant 1er juillet) et récent (à partir du 1er juillet), ainsi
que chaque action, chaque scénario, le nombre de dates et les rejets. Le modèle
roulant continue à n'utiliser que les sessions antérieures, sans modification
de seuil entre segments. Les jours de warm-up restent dans le dénominateur
économique de 180 jours. Proxy /30 jours moins 20 $ infra hypothétiques ; cible
utilisateur 150–200 $ nets pour 1 000 $. Aucune dépense engagée.

Pour poursuivre une direction, exiger >=20 dates par segment, moyenne et PnL
positifs dans les deux segments et tous les scénarios payants, IC bootstrap
97,5 % de moyenne (blocs de trois semaines calendaires, 10 000 tirages,
seed 20260907) strictement positif, PF >=1,2, proxy mensuel >=30 $ après infra
comme filtre de recherche, pas comme accomplissement de la cible utilisateur.
Un effectif insuffisant ne valide rien. Corriger les bogues documentés, sans
changer l'hypothèse après résultat. Un échec suspend cette règle.

Sources primaires : [frais trade.xyz](https://docs.trade.xyz/trading/fees),
[Strategy et exposition BTC](https://www.strategy.com/learn). Une exposition
à BTC ne rend pas MSTR interchangeable avec BTC.
