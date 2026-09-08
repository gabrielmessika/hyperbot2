# Pression agressive externe : signal exploratoire, edge non confirmé

Les champs de volume acheteur agressif Binance USDC ont été réutilisés sans
appel réseau supplémentaire. Deux règles préenregistrées, exécution théorique
sur Hyperliquid à l'heure suivante, six mois BTC/ETH/SOL, horizon principal 6 h.

| Règle | N | Net moyen | Stress coûts | Retard 1 h | PF | IC 97,5 % |
|---|---:|---:|---:|---:|---:|---|
| Flux accepté par le prix | 109 | +17,05 bps | +2,05 bps | +11,83 bps | 1,42 | [−6,67 ; +42,77] |
| Flux absorbé, prix peu mobile | 14 | −19,45 bps | −34,44 bps | −34,34 bps | 0,68 | échantillon insuffisant |

Le flux accepté reste positif avec funding adverse (+16,43 bps), après retrait
du meilleur événement et dans cinq blocs de 30 jours sur six. Longs et shorts
contribuent positivement. ETH produit 1 438,79 des 1 858,16 bps cumulés, BTC
+433,61, SOL −14,25 : concentration importante. Le seuil de confiance n'est
pas atteint, donc **HYPOTHESIS_NOT_CONFIRMED** selon les gates enregistrées.
L'absorption est négative même sans frais/funding et n'est pas retenue.

## Intérêt économique pour 1 000 $

La somme des rendements d'événements n'est pas une performance de portefeuille.
Une simple mise à l'échelle constante de 50 $ par événement donnerait 9,29 $
de PnL sur les 173 jours évaluables, soit 1,61 $ par tranche de 30 jours avant
coût serveur, sans arrondis, stops ni réduction de risque. En coûts stressés,
cette même approximation ne laisse qu'environ 0,19 $ par 30 jours.
Ce calcul illustratif suffit à montrer que le résultat brut positif ne justifie
pas à lui seul un déploiement. Le budget serveur de 20 $/mois des précédents
rapports est une hypothèse, pas une nouvelle dépense ou facture vérifiée.

Pas de sélection d'ETH seul ou de changement d'horizon. Une extension gratuite
pourrait tester la stabilité du mécanisme, mais les critères statistiques et
économiques actuels ne justifient pas de qualifier un bot rentable.
La prochaine recherche porte sur une marge économique potentiellement plus
large, dans les fundings d'un univers élargi, avec un nouveau protocole.

Reproduction : `rtk proxy uv run python scripts/investigate_order_flow.py
--output <nouveau_dossier>`. Résumé checksumé dans ce dossier, événements et
provenance dans `data/order_flow_2026-09-07/run1/`. Les grilles prix/funding et
0 <= volume acheteur <= volume total sont contrôlés. Aucun serveur modifié.

Limites : flux d'un contrat USDC, pas la totalité de Binance ; prix déjà
consultés, correction limitée à deux règles ; opens hypothétiques sans preuve
de réception/exécution ; funding HL au proxy horaire ; aucune simulation de
portefeuille ni garantie de rendement.
