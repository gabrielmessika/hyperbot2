# Point de coût à instruire, sans nouveau résultat de stratégie

L'audit de microstructure a conduit à relire les frais HIP-3. Les expériences
week-end/nocturne appliquaient 9 bps de frais par côté en base, et signalaient
que l'historique des paramètres de frais n'était pas qualifié.

Le snapshot natif existant `data/weekend_repricing_2026-09-07/xyz_meta.json`
affiche `growthMode=enabled` et `deployerFeeScale=1.0` pour TSLA, NVDA, HOOD,
COIN, META, AMZN. MSTR n'affiche pas growth mode. La
[documentation du déployeur](https://docs.trade.xyz/trading/fees) indique
0,0090 % taker de base sous growth mode, soit **0,9 bp**, contre 0,090 % /9 bps
au tarif standard. Elle cite MSTR parmi les exclusions de ce mode.

Il faut donc examiner les stratégies inchangées sous ce coût actuel avant de
rejeter globalement leur économie. Ce n'est pas une autorisation de choisir
des frais artificiellement bas. Conserver les anciens résultats comme scénario
standard, puis calculer une sensibilité documentée au tarif observé.

L'état actuel ne prouve pas que growth mode était actif à chaque instant passé.
`lastFeeScaleChangeTime` ne doit pas être interprété sans preuve comme date
d'activation de growth mode. L'historique doit être recherché gratuitement ;
à défaut, le résultat doit rester une simulation aux conditions de frais
actuelles, sans prétention à reproduire les factures historiques.

Aucun nouveau signal, aucun PnL avec frais modifiés ni aucune sélection d'actif
n'ont encore été calculés dans cette note. La prochaine passe doit enregistrer
le protocole de sensibilité avant calcul et conserver les gates statistiques,
de retard, de concentration et de capacité déjà établies.
