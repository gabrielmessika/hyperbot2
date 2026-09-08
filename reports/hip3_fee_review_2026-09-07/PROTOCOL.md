# Sensibilité des stratégies actions aux frais observés

Enregistrement le 7 septembre 2026, avant recalcul. Aucune nouvelle règle de
signal : reprendre tous les événements publiés des expériences week-end
(univers initial puis COIN/MSTR) et nocturne (ancien puis validation), pour
fade et follow. Aucun changement de coin, date, direction, seuil ou horizon.

Sources : snapshot natif `xyz_meta.json` déjà acquis, barèmes officiels
Hyperliquid et trade.xyz ; annonce officielle 481 du 24 novembre 2025 indiquant
l'activation du growth mode par trade.xyz. Cette annonce renforce la plausibilité
du tarif mais ne remplace pas une timeline complète par marché. Présenter
explicitement une sensibilité aux conditions actuelles, pas une facture passée.

1. Garder les résultats standards publiés (9 bps base /18 bps stress par côté).
2. Tarif étudié : appliquer la formule officielle au snapshot, sans remise de
   staking, volume, referral ou builder. Avec scale=1 et growth enabled, 0,9 bp
   base /1,8 bp stress ; MSTR conserve 9/18 bps. Les six autres actifs du test
   doivent avoir l'état enabled dans le snapshot, sinon échec explicite.
3. Recalculer uniquement les frais de chaque événement/scénario. Slippage,
   funding, prix, délais et événements inchangés. L'économie de frais doit
   correspondre exactement au prorata du notional entrée+sortie, pas à une
   soustraction arbitraire de 16,2 bps indépendante de la variation de prix.
4. Vérifier le calcul contre `leg_return` sur les bougies brutes de chaque
   événement. Préserver les artefacts d'origine. Aucune nouvelle requête de prix.
5. Réutiliser les statistiques et bootstrap originaux, séparations inchangées.
   Gates d'origine : tous scénarios de coût positifs, PF>1,2, intervalle corrigé
   inférieur >0, stabilité des blocs (5 week-end /3 nocturne), résultat positif
   sans le meilleur événement. Aucune promotion grâce au meilleur sous-ensemble.
6. Publier la concentration par actif et un proxy économique sans levier :
   50 $ par événement, ainsi que 1 000 $ de notional TOTAL répartis également
   entre les signaux simultanés ; capital constant, sans réinvestissement.
   Retrancher une hypothèse explicite de 20 $/mois d'infrastructure. Le proxy
   n'est pas un backtest de marge/exécution et ne suffit pas à promouvoir.
7. Lancer une validation supplémentaire seulement si les gates statistiques et
   de stabilité passent dans les segments nécessaires et si le proxy total
   plafonné dépasse 30 $/30 jours après infra. Les exigences de risque, profondeur,
   oracle, corporate actions et exécution réelle restent à vérifier ensuite.

Si un tarif plus réaliste ne suffit pas, conserver le constat et passer à une
autre hypothèse. Aucun live ni achat. Aucun rendement garanti.
