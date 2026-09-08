# Sortie de compression avec volume — protocole avant calcul

Hypothèse : une cassure après contraction de l'amplitude peut se prolonger
pendant la journée suivante. Aucun caractère prédictif établi. Réutiliser les
18 altcoins natifs complets du 10 mars au 6 septembre 2026 exclusif, sans
CASHCAT ni sélection supplémentaire. Univers courant et période déjà examinée :
recherche exploratoire, pas holdout. Aucun nouveau téléchargement ni achat.

## Signal fixé

Pour une entrée dans la bougie horaire i, la bougie signal est i−1, clôturée.
La boîte de compression contient les **24 bougies i−25 à i−2**. Son amplitude
normalisée est (plus haut −plus bas)/open de la première bougie. Comparer à la
médiane de **sept blocs de 24 heures précédents**, sans chevauchement avec la
boîte : i−193 à i−26. Compression si amplitude de la boîte positive et au plus
**la moitié** de cette médiane.

Acheter si le close signal dépasse le plus haut de la boîte et son propre
open ; vendre s'il passe sous le plus bas et son propre open. Le volume signal
doit atteindre **deux fois** le volume médian des 24 heures de la boîte,
lui-même strictement positif. Aucun indicateur d'une bougie future consulté.

Conserver **24 heures**, sans resserrement d'un stop ou inversion selon le PnL.
Espacer les signaux retenus d'au moins **25 heures par actif**, même si une
entrée est ensuite refusée pour budget. Sortie finale, y compris retard,
couverte par le dataset. Aucun choix d'horizon ou de sens après résultat.

Contrôle préenregistré : même cassure, volume et espacement, **sans condition
de compression**. Mesurer si cette condition apporte quelque chose ; le contrôle
ne sera pas promu opportunément d'après son classement.

## Portefeuille et risque

Moteur `simulate_portfolio` existant, capital 1 000 $, plafonds bruts à l'entrée
**0,5x /1x /1,5x**, budget disponible partagé entre signaux simultanés et plafond
par actif d'un tiers du cap. Quantités natives arrondies, minimum 10 $, positions
simultanées, funding et coûts. Pas de rebalancement gratuit ni de martingale.
Marge cross hypothétique, levier de configuration fixe 2, maintenance stress
20 % du notional ; vérifier le snapshot natif et conserver ses limites.

Arrêt définitif au drawdown observé de **20 % depuis le sommet**, latent et coûts
inclus, liquidation simulée au prochain open+60 s, dépassements conservés.
Publier aussi l'enveloppe OHLC avant/après transactions et les tests de marge.
Le cap d'entrée ne garantit pas un levier constant pendant la détention.

Exécution open+60 secondes au prix open supposé, frais taker 4,5 bps et
slippage 2 bps par côté. Scénarios : central, coûts 9/5, retard 1 h à l'entrée
et à la sortie, funding adverse, contrôle zéro coût. Paiements timestampés,
oracle de funding approché par open. Infrastructure 0 et 20 $/30 jours
hypothétiques, aucune dépense engagée. Les [frais natifs](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees)
et le [funding](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding)
sont documentés officiellement ; aucune remise personnelle supposée.

## Décision

Courbe continue sur 180 jours sans reset mensuel. Publier net cumulé, mensuel
équivalent, drawdown observé/enveloppe, temps sous sommet, mois rouges/verts,
contributions, pertes extrêmes et refus. Un mois rouge n'est pas un veto.
Filtre préliminaire : quatre scénarios payants globalement positifs,
enveloppe <=20 %, marge observée et enveloppe sans rupture. Le passage de ce
filtre seul ne prouve pas un rendement intéressant de 15–20 % mensuels.

Si candidat économiquement pertinent, poursuivre avec concentration, autre
période gratuite et qualification d'exécution. Sinon conserver le résultat et
changer de mécanisme ; ne pas retirer des actifs perdants ou ajuster les seuils.
Résultats reproductibles avec SHA-256 du protocole, code et sources. Aucun GO
sans ces qualifications, aucun changement live, ancien bot ou serveur.
