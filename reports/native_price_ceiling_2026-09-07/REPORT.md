# La règle acheteuse échoue aussi sur les données natives 2025 disponibles

**`NATIVE_PRICE_CEILING_CROSS_PERIOD_SCREEN_FAILED`.** Le problème ne se
réduit pas au transfert de plateforme : sur les neuf actifs qualifiés,
la même règle acheteuse perd sur Hyperliquid 2025 avant tout débit de funding.
Aucune collecte annuelle de funding ni simulation de capital n'est justifiée
par le filtre enregistré. Aucun nouveau paramètre recherché.

[Protocole](PROTOCOL.md), [enregistrement avant calcul](registration.json).
Univers défini par disponibilité native avant ce PnL : ARB, BNB, DOGE, INJ,
LINK, NEAR, UNI, WLD, XRP. XMR/ZEC restent dans les anciennes études conservées.
Ce changement d'univers ne constitue pas une validation indépendante de celles-ci.

Chaque lundi : acheter les trois volatilités journalières les plus faibles
et les trois plus fortes sur trente rendements passés, six poids égaux,
garde de 168 h. Contrôle : acheter les neuf actifs aux mêmes dates.
Bougies 4 h natives pour 2025 ; regroupement sans interpolation des quatre
bougies horaires complètes pour 2026. Les clôtures quotidiennes utilisées
par les signaux sont identiques à celles du calcul horaire en 2026.

| Panneau Hyperliquid | Paniers | Prix brut moyen | Après frais/slippage centraux | Coûts renforcés | Retard 4 h |
|---|---:|---:|---:|---:|---:|
| Année 2025 | 47 | −95,53 bps | **−108,45 bps** | −123,34 bps | −67,33 bps |
| 204 jours en 2026 | 23 | +144,06 bps | **+130,94 bps** | +115,80 bps | +123,12 bps |

Ces valeurs sont des moyennes par panier, rapportées au notionnel brut engagé.
100 bps valent 1 %. Elles ne sont ni des dollars de gain ni un rendement
mensuel du compte. Funding fixé à zéro dans tous les cas. Central : frais
4,5 bps et slippage 2 bps par côté ; coûts renforcés 9/5. Le retard est de
4 h, explicitement différent de l'ancien scénario horaire.

Le scénario de funding adverse ne peut qu'ajouter des débits au plafond
présenté ici. Les résultats négatifs 2025 suffisent donc à échouer au filtre
de robustesse de cette règle. Le funding signé pourrait produire des recettes :
sa rentabilité n'est pas calculée et n'est pas bornée par ce diagnostic.

En 2025, 23 paniers sur 47 sont positifs, mais le pire perd 27,59 % du
notionnel brut. L'intervalle bootstrap 95 % de la moyenne centrale vaut
[−388,50 ; +202,52] bps. En 2026 : onze gains sur 23, pire panier −11,72 %,
intervalle [−170,09 ; +502,80] bps. Les deux bornes inférieures sont négatives.
Le contrôle des neuf actifs ne résout pas le problème : central −69,65 bps
en 2025 contre +129,12 en 2026, toujours sans funding.

[Reproduction](reproduction.json) : huit artefacts identiques, 420 agrégats
de paniers contrôlés ; 1 890 vérifications de résultat par registre cash signé
indépendant du calculateur `leg_return`. Les 23 classements et scores 2026
retrouvent exactement la fonction horaire existante. Huit tests ciblés des
briques réutilisées passent ; lint et format du nouveau script vérifiés.
Le hash de configuration, les sources et les versions sont conservés.

Ce contrôle n'est pas un portefeuille : aucun drawdown du compte, marge,
minimum de trade, lot, tick ou fill réel n'est validé. Périodes déjà réutilisées,
choix successifs de recherche et changement d'univers limitent l'inférence.
Les barres 4 h ne reconstituent pas la trajectoire horaire manquante.

[Verdict](review.json) : piste acheteuse non retenue, objectif économique
non atteint. Aucun appel réseau, achat, ordre réel ou changement serveur.
Calcul et reproduction terminés ; aucune extension de la campagne engagée.
