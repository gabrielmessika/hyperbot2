# SKHX : historique gratuit exploitable pour un premier test

**4 320 heures de prix et de funding sur 180 jours**, du 10 mars au
6 septembre 2026 exclusif. Dix appels publics, 1 000 052 octets, coût nul.
NVDA possède déjà la même couverture localement. Aucun rendement calculé à ce
stade, aucun GO. Client et chargeur strict existants réutilisés.

Identités, intervalles OHLC, hashes, continuité des heures et unicité des
paiements vérifiés. Funding décalé de 0 à 261 ms par rapport à l'heure ronde.
SKHX compte 24 bougies de volume nul, listées dans `acquisition_summary.json` ;
ne pas simuler un fill à ces prix. NVDA n'en compte aucune.

## Contrat, horaires et limites

SKHX suit une action ordinaire SK Hynix divisée par le taux USD/KRW. La page
courante indique des prix externes de 08:10–08:50, 09:01–15:30 et 15:40–20:00
KST. La première fenêtre commence donc la veille à 23:10 UTC, avant la séance
principale. L'index de recherche conserve une ancienne version 08:00/09:00 ;
la page courante présente aussi des intervalles internes ne couvrant pas
explicitement toutes les minutes intermédiaires. Aucun calendrier historique
exact à la minute n'est démontré. [Source XYZ Corée](https://docs.trade.xyz/asset-directory/stocks/korea)

Sans prix externe, l'oracle utilise les prix d'impact internes avec une moyenne
exponentielle ; il reprend la référence externe au tick suivant son retour.
Il ne faut donc pas traiter un ancien prix cash figé comme une offre exécutable
avant ouverture. [Source oracle XYZ](https://docs.trade.xyz/perp-mechanics/oracle-price)

Le snapshot natif indique SKHX maxLeverage 10, szDecimals 3, growthMode activé,
deployerFeeScale 1. Le tarif taker courant sans remise est 0,9 bps par côté ;
tester également 9 bps si le mode growth ne s'applique pas historiquement.
Le niveau de marge autorisé n'est pas une taille recommandée. La documentation
de spécification classe SKHX en marge isolée normale : les hypothèses cross
du portefeuille crypto précédent ne doivent pas être reprises telles quelles.
[Frais XYZ](https://docs.trade.xyz/perp-mechanics/fees),
[spécifications XYZ](https://docs.trade.xyz/consolidated-resources/specification-index).

## Suite

Un test horaire causal peut mesurer un éventuel rattrapage relatif SKHX/NVDA
en traversant la préouverture, sans prétendre identifier le tick de transition.
Enregistrer avant calcul fenêtre, modèle, seuil, sens, coûts et retard ; exclure
les fermetures publiées et conserver toutes les exclusions de données. Si le
résultat net est intéressant, vérifier ensuite portefeuille, latent/drawdown
20 %, marge isolée, concentration et exécution avec les archives gratuites.
Les dates de jours fériés viennent de la [page officielle XYZ](https://docs.trade.xyz/consolidated-resources/holiday-closures).

`quality.json` reproduit exactement offline ; snapshots documentaires conservés
et checksumés dans `data/korea_opening_2026-09-07/documentation`. Aucun achat,
ordre, secret consulté, service ou serveur modifié. Recherche active.
