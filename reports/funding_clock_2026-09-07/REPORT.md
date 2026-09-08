# Règlements de funding : effet temporel non confirmé

**Le premier filtre échoue, sans justifier de construire un portefeuille.**
Sur 113 événements répartis sur 62 jours de 2025, la règle perd en moyenne
21,81 bps après coûts et 8,79 bps même sans coûts. L'entrée de contrôle
deux heures plus tard fait mieux, mais devient négative avec coûts renforcés.

## Hypothèse et causalité

Le funding est un transfert périodique entre positions longues et courtes,
avec des intervalles pouvant varier selon le contrat. [Documentation Binance](https://www.binance.com/en/support/faq/detail/360033525031).
L'effet de prix après un règlement important était l'hypothèse à tester.

Signal choisi uniquement à partir du paiement précédent : si son taux absolu
atteint 10 bps, prévoir le prochain règlement à partir de son intervalle
de 4 ou 8 heures. Long pour un taux précédent positif, short pour un taux
négatif. Entrer à l'horaire prévu +60 secondes, prix proxy open horaire,
sortir une heure plus tard. Le taux du règlement à venir ne sélectionne
jamais l'événement ni sa direction. Aucun signal obtenu à partir d'un taux
connu seulement après l'entrée.

Contrôle apparié : même signal et direction, entrée deux heures plus tard,
sortie après une heure. Stress de retard : fenêtre principale décalée d'une
heure. Les prix des trois sorties doivent être disponibles avant de retenir
un événement. Une éventuelle erreur de prévision d'horaire est conservée,
sans supprimer rétrospectivement le signal selon les paiements futurs.

## Données et événements

Réutilisation intégrale des archives publiques Binance de 15 actifs sur 2025,
qualifiées lors du transfert précédent : 8 760 bougies par actif, zéro trou
ou volume nul, funding et intervalles contrôlés. Aucune acquisition nouvelle.
Tous les 113 horaires prévus coïncident avec un paiement réalisé.

39 signaux longs et 74 shorts. Répartition : ZEC 50, XMR 45, ENA 11,
FARTCOIN 3, INJ/JUP/TAO/WLD un chacun. Les autres actifs ne déclenchent aucun
signal. ZEC et XMR représentent donc 95 événements sur 113 ; cette
concentration reste visible, sans retrait des actifs perdants.

## Résultats en bps du notionnel d'entrée

| Scénario | Fenêtre principale | Contrôle à +2 h |
|---|---:|---:|
| Central : frais 4,5 /slippage 2 bps par côté | −21,81 | +7,09 |
| Coûts renforcés : 9 /5 bps | −36,84 | −7,91 |
| Principale retardée de 1 h | −11,24 | +7,09 |
| Funding adverse | −21,81 | +7,09 |
| Sans coûts | −8,79 | +20,08 |

Quantité constante par notionnel initial ; frais calculés à l'entrée et à
la sortie. Le funding n'est compté que pendant la détention. Les fenêtres
observées ne contiennent aucun paiement : l'entrée principale suit le
règlement et la sortie précède le suivant. Aucun revenu du paiement
antérieur n'est crédité ; le scénario funding adverse égale donc le central.

Profit factor central 0,672. Pire événement −498,46 bps, soit environ
−4,98 % du notionnel en une heure. Ce chiffre n'est pas un drawdown de
compte de 1 000 $. La moyenne principale est inférieure au contrôle de
28,90 bps par événement. Le contrôle positif en central n'est pas promu
comme nouvelle stratégie : il échoue au stress de coûts et a été examiné
dans le cadre de cette même recherche.

Bootstrap descriptif, 5 000 tirages par blocs de 7 jours, calendrier complet
avec jours sans événement : intervalle 95 % de la moyenne centrale
**[−54,35 ; +21,04] bps**. Intervalle de la différence appariée principale
moins contrôle : **[−71,18 ; +17,53] bps**. Non corrigés pour les recherches
antérieures, ni prédictifs, ni preuve d'une causalité du règlement.

## Décision

**FUNDING_CLOCK_HYPOTHESIS_NOT_CONFIRMED**. Le nombre minimal d'événements et
de jours est atteint, mais les scénarios payants sont négatifs et la borne
inférieure de l'avantage apparié n'est pas positive. La règle est suspendue
sans inversion de signe, nouveau seuil ou horaire choisi après résultat.

Ce filtre n'a simulé ni capital partagé, ni lots/minimums, ticks, marge ou
liquidité réelle. Il ne fournit donc aucun rendement mensuel ni respect
du plafond de drawdown 30 %. Les données Binance et les frais Hyperliquid
de référence restent des hypothèses de transfert, sans preuve de fills
natifs. Aucun portefeuille ou téléchargement de réplication supplémentaire
n'est justifié par ce résultat négatif.

Prochaine piste : un modèle statistique conditionnel simple, entraîné
uniquement sur une fenêtre passée et évalué chronologiquement sur les
semaines suivantes. Fixer variables, régularisation, horizon et seuil
économique avant calcul, purger les labels non encore connus et conserver
les coûts et contraintes de risque. Les données 2025/2026 déjà explorées
ne deviendront pas une validation prospective du seul fait d'utiliser un
modèle ; aucune recherche de paramètres sur les fenêtres d'évaluation.

## Livraison

Réutilisation de la comptabilité événementielle et du bootstrap existants.
Six nouveaux tests pour signal ex ante, horaire, bornes de couverture,
observations invalides et inclusion exacte des paiements. Suite complète
**310 tests**, lint/format **298 fichiers**, mypy **72 sources** passent.
Trois artefacts reproduits à l'identique, sources/configuration checksumées,
protocole enregistré avant PnL. Aucun nouvel appel de marché, achat, ordre
réel, service ou serveur modifié. Consultation documentaire publique seule.
Tous les calculs sont terminés ; recherche active, aucun GO.
