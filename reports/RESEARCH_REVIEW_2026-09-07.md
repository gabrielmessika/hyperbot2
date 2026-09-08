# Bilan économique et coût de la recherche

## Réponse à la demande de bilan

**Aucune piste n'est validée pour engager le capital. Aucun bot rentable
répondant à l'objectif n'est livré.** Plusieurs résultats historiques sont
positifs, mais aucun candidat examiné ne fournit à la fois une rentabilité
robuste entre périodes, une résistance aux coûts et un risque compatible avec
le plafond de recherche de 30 %. La cible de 10 % mensuels n'est pas démontrée.

Le compteur de l'objectif consulté lors de ce bilan indique **3 032 073 tokens
et 34 271 secondes**, soit environ 9 h 31. Il ne fournit pas la facture en
dollars. Le coût en tokens ne doit pas être assimilé aux dépenses de données :
les dernières acquisitions étaient gratuites, mais la recherche elle-même
consomme des ressources importantes.

## Résultats qui pouvaient sembler prometteurs

Montants cumulés pour des simulations initialisées à 1 000 $, après coûts
de trading/funding et sans coût marginal supplémentaire de serveur. Les durées
et univers diffèrent ; il ne s'agit pas d'un classement de performances comparables.

| Piste | Résultat favorable observé | Épreuve qui empêche la validation |
|---|---|---|
| Cassures + rotation hebdomadaire, exposition 1,5x | Hyperliquid 18 actifs, 204 jours 2026 : +538,26 $ | Transfert Binance 15 actifs 2025 : −270,83 $, arrêt dès le 19 janvier ; enveloppe de drawdown 38,88 %. Le sous-panel natif 15 dépasse également 30 % dans certains stress. |
| Panier acheteur, exposition 0,5x | Binance 2025 : +180,65 $ ; Hyperliquid 204 jours 2026 : +201,11 $ | Binance 2024 : arrêt avec enveloppe 31,77 % et seulement +6,19 $ ; funding adverse négatif. |
| Panier acheteur conditionné par la tendance, exposition 0,5x | Binance 2024–2025, 731 jours continus : +582,16 $, équivalent 1,90 % mensuel | Hyperliquid 204 jours 2026 : +2,29 $, équivalent 0,034 % mensuel ; légèrement négatif sous coûts renforcés et funding adverse. |

Sources : [transfert du portefeuille](prior_transfer_2026-09-07/REPORT.md),
[diagnostic du capital acheteur](volatility_capital_2026-09-07/REPORT.md),
[condition de tendance](collective_trend_2026-09-07/REPORT.md).
Les transferts Binance utilisent des hypothèses d'exécution Hyperliquid ;
ils ne sont pas présentés comme des historiques natifs Hyperliquid.

Le dernier [carry hebdomadaire](weekly_carry_2026-09-07/REPORT.md) est déjà
négatif au niveau des événements, avant toute justification de levier :
−11,51 bps par panier sur 2024–2025 et −25,50 bps sur Hyperliquid 2026.
Le funding reçu est absorbé par les pertes de prix et les frais.
Le diagnostic maker avait, lui, échoué sur les conditions de données et
d'exécution nécessaires ; il n'avait pas établi une rentabilité négative
de tout market making possible.

## Ce qui a mal fonctionné dans la conduite de la recherche

L'exploration a été prolongée de variante en variante, avec beaucoup de code,
de rapports et de vérifications, sans limite de ressources liée à la valeur
économique attendue de l'expérience suivante. L'instruction de chercher un
edge ne justifie pas de poursuivre indéfiniment la même méthode.

La vérification comptable et les tests évitent des résultats techniquement
faux ; leur multiplication ne crée pas un avantage de trading. La réutilisation
des mêmes périodes pour choisir les hypothèses suivantes accroît également
le risque de sélectionner un résultat chanceux. Les enregistrements avant
calcul de chaque variante ne rendent pas ces périodes indépendantes de la
recherche cumulative.

Les données et outils sont réutilisables, mais ils ne constituent pas la
livraison économique demandée. Le temps déjà dépensé ne justifie ni de
promouvoir un candidat fragile ni d'engager de nouvelles dépenses.

## Décision immédiate

La nouvelle étude de choc collectif est **suspendue avant enregistrement
et avant calcul de PnL**. Un brouillon de module, de tests et de protocole
existe ; aucun driver d'expérience ni jeu de résultats n'a été produit.
Ne pas la présenter comme testée ou comme prochaine action automatique acquise.
Aucune nouvelle vague de simulations n'est engagée dans ce bilan.

L'objectif économique reste non atteint ; aucun GO, aucune activation live,
aucun achat ni changement serveur. Ce constat ne prouve pas qu'un bot rentable
sur Hyperliquid est impossible. Il signifie que cette recherche n'en a pas
identifié et ne justifie pas de continuer à l'identique sans revoir sa méthode
et son coût. Toute éventuelle reprise doit être bornée et motivée par une
information nouvelle, pas seulement par une nouvelle combinaison d'indicateurs.
