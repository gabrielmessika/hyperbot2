# Rotation hebdomadaire de force relative

Test enregistré avant calcul. Réutiliser les 180 jours natifs complets des
18 altcoins hors CASHCAT, du 10 mars au 6 septembre exclusif. Univers courant
déjà sélectionné et données déjà examinées : étude exploratoire, pas holdout.
Aucun achat, nouvel appel de données, ordre ou changement serveur.

## Règle figée

Chaque **lundi à 00:00 UTC**, classer les actifs sur leur rendement des sept
jours précédents, en excluant les dernières 24 heures : close[i−25] /
close[i−193] −1 pour une entrée dans la bougie i. Acheter les **trois premiers**,
vendre les **trois derniers**, poids notionnels égaux avant arrondis. Départager
les égalités par symbole ; ne pas agir si les scores des deux groupes ne sont
pas strictement séparés. La force est relative : un actif négatif peut rester
dans le groupe acheteur si les autres baissent davantage.

Conserver **168 heures**. Fermer puis rouvrir au prochain classement, même si
un actif reste sélectionné ; facturer cette rotation complète. Pas de passage
à un autre lookback, jour de semaine, sens ou sous-univers après résultat.

Le panier est équilibré en dollars avant arrondis, pas garanti neutre en bêta.
Les gains/pertes et le funding de chaque jambe sont calculés séparément.

## Portefeuille et comparaison

Moteur existant, capital initial 1 000 $, plafonds bruts d'entrée **0,5x /1x /
1,5x**, budget partagé également entre les six jambes. Quantités natives
arrondies vers le bas, minimum 10 $, plafond d'un tiers par actif déjà présent
dans le moteur. Pas de rebalancement gratuit ou de martingale. Le notional
peut dériver avec les prix pendant la semaine.

Entrée/exit open+60 s au prix open hypothétique ; retard 1 h en stress.
Paiements de funding timestampés, oracle approché par l'open. Frais/slippage
centraux 4,5/2 bps par côté ; coûts renforcés 9/5 ; funding adverse ; contrôle
sans coût. Infrastructure 0 et 20 $/30 jours hypothétiques, débités chaque heure.
Marge cross hypothétique à levier de configuration fixe 2, maintenance stress
20 % du notional, métadonnées courantes vérifiées. Arrêt définitif au drawdown
observé de 20 %, sortie au prochain open+60 s, dépassements conservés.

Comparateur : panier long des 18 actifs, acheté au premier lundi admissible,
conservé jusqu'au dernier open+60 s, mêmes scénarios/arrondis/risque. Ne pas le
promouvoir comme autre stratégie selon son résultat. Les sorties des positions
hebdomadaires doivent être couvertes dans la fenêtre, y compris avec retard.

## Mesure et décision

Courbe continue sur 180 jours, sans remise à zéro mensuelle. Publier résultat
net, équivalent mensuel composé non prédictif, drawdown observé et enveloppe
OHLC, marge, contribution des actifs, mois, temps sous le sommet et arrêts.
Un mois rouge n'est pas un veto. Passage du filtre : les quatre scénarios
payants globalement positifs, enveloppe <=20 %, aucun problème de marge.
Un petit profit ne démontre pas l'objectif économique de 15–20 % mensuels.

Même en cas de passage, il faut d'autres preuves gratuites et une qualification
d'exécution avant un GO. Conserver les échecs et reproduire offline les artefacts
avec hashes de code, protocole et sources. Ne pas sauver un échec en choisissant
un nouvel horizon ou en inversant les groupes après coup.
