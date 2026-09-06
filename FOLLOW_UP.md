# HyperBot2 — suivi de l’implémentation

Date : 6 septembre 2026. Développement autorisé ; aucun déploiement ni live.

| Lot | Statut |
|---|---|
| P0 — reprise autonome des composants et tests HyperBot | Livré : package autonome, provenance, 82 tests hérités |
| P1 — métadonnées outcomes, qualification, collector rapide | Outils livrés ; témoin 40 s terminé ; qualification réelle `DATA_BLOCKED` |
| P2 — screening legacy et campagne bornée | Livré : 892 492 lignes relues, runner 18 scénarios ; candidat réel `DATA_BLOCKED` |
| P3 — stratégie, portefeuille, replay/shadow, gates | V0 de simulation livrée et testée ; qualification maker non acquise |
| Validation économique A/OOS et shadow continu | Non acquise |
| Canary et live | Bloqués, non implémentés |

Les services existants restent arrêtés. Les données legacy ne sont jamais
promues automatiquement en preuves de fills maker.

## Livraison

Voir [README](README.md), [contrats d’entrée](docs/DATA_CONTRACT.md) et
[rapport complet](reports/implementation_2026-09-06/REPORT.md). La configuration
refuse le live. Chaque campagne est bornée et sans relance automatique ; les
répertoires de run existants ne sont pas écrasés. La reprise de portefeuille
après interruption et le daemon shadow permanent ne sont pas implémentés.

Le noyau HyperBot est copié : stockage, contrats d’événements, collector,
replay, risque, adaptateurs et recherche. Les modifications ciblées portent
sur `fast=true`, PF par cycle et bootstrap journalier commun aux cryptos.
La comptabilité outcomes et l’interface de campagne sont nouvelles.

## Prochaine décision fondée sur les données

Ne pas lancer une collecte permanente. Les deux essais réels terminés donnent
`DATA_BLOCKED` : frais/spécifications historiques et référence causale non
qualifiés, queue maker non validée, et 0/591 carnets admissibles à l’activation
dans le témoin local avec les latences du plan. La suite exige des preuves
ciblées pour ces gaps, pas davantage de raw BTC sans hypothèse outcomes.
Les bornes de risque, l’abstention et les gates de la fondation restent inchangés.
