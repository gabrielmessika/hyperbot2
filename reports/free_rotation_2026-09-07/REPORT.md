# Trois nouvelles pistes, uniquement avec des données gratuites

**Aucune des trois règles ne mérite de passer à l'exécution à ce stade.**
La préférence utilisateur est enregistrée dans `AGENTS.md` : aucune nouvelle
dépense de recherche ; suspendre les pistes exigeant un accès payant et passer
à d'autres mécanismes. Les propositions d'achat précédentes sont abandonnées.

Cette passe a effectivement testé trois règles nouvelles, puis prolongé la
seule qui paraissait intéressante sur davantage d'historique **gratuit**.
Pas de nouveau bot, d'achat, de clé utilisée ou de modification serveur.

## Premier filtre sur les archives existantes

BTC/ETH/SOL/HYPE, 180 jours horaires du 10 mars au 6 septembre 2026 UTC
exclusif ; 30 jours de chauffe. Règles fixées [avant calcul](PROTOCOL.md).
Frais taker 4,5 bps + slippage supposé 2 bps par côté, funding signé réalisé.
Un bps vaut 0,01 % du **notionnel brut du panier**, pas du capital de 1 000 $.

| Règle | Paniers | Moyenne nette/panier | Coûts stressés | Conclusion |
|---|---:|---:|---:|---|
| Force relative 7 j : acheter le meilleur, vendre le moins bon, tenir 24 h | 149 | +4,87 bps | −10,18 bps | Trop fragile ; PF 1,08 et seulement 2/5 blocs positifs |
| Portage relatif : acheter le funding le plus faible, vendre le plus élevé, tenir 24 h | 147 | −12,71 bps | −27,74 bps | Écartée ; PF 0,81, prix seuls déjà légèrement négatifs |
| Tendance 30 j, positions conservées 7 j | 21 | +98,96 bps | +83,77 bps | Positive mais trop peu de semaines : extension gratuite immédiate |

Le portage saute deux dates où les scores sont tous égaux. Chaque panier
ferme avant le suivant ; la dernière date est exclue si le stress de délai
ne dispose pas d'un prix de sortie. Aucun turnover fictif ou remplissage maker.

La force relative a un intervalle bootstrap exploratoire 98,33 % de
[−29,34 ; +44,66] bps par panier ; portage [−37,21 ; +11,71]. La correction
porte sur les trois règles de cette passe, sans effacer les recherches
antérieures. Les permutations de signaux ne fournissent pas de résultat
convaincant ; elles restent un diagnostic, pas une identification causale.
Voir [résumé complet des trois règles](initial_summary.json).

## Extension gratuite : 640 jours communs et 60 semaines supplémentaires

La limite native de 5 000 bougies s'applique à chaque intervalle : les bougies
quotidiennes permettent ici d'aller beaucoup plus loin que les horaires.
Quatre requêtes publiques ont fourni 644 jours BTC/ETH/SOL et 640 HYPE.
L'alignement a d'abord échoué : HYPE commence le 5 décembre 2024. L'ajustement
à l'intersection des quatre couvertures a été [enregistré explicitement](COVERAGE_ADJUSTMENT.md)
avant le premier calcul de rendement ancien, sans changer la règle ni l'univers.
[Contrat de l'API native](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint).

Fenêtre complète : **5 décembre 2024–6 septembre 2026 exclusif**, 640 bougies
quotidiennes par actif. Signal toujours 30 jours, détention sept jours, entrées
le jeudi comme lors du premier filtre. Cela donne 86 paniers : 60 entièrement
dans l'ancien segment, 25 dans les 180 jours déjà consultés et un à cheval
sur la frontière. Ces segments sont publiés séparément ; ce n'est pas un test
prospectif indépendant d'une stratégie jamais sélectionnée.

Le filtre avant coûts sur les 60 anciennes semaines était positif (+62,82 bps
en moyenne), ce qui justifiait de compléter le funding. **92 requêtes gratuites**
ont récupéré la période manquante antérieure au 10 mars ; les taux déjà locaux
sont réutilisés ensuite. 15 360 taux horaires par actif, sauf HYPE : 15 350.
Les dix heures absentes sont le 5 décembre 2024, avant 10:00 UTC, entièrement
hors des positions évaluées et de leurs paiements. Le collecteur a signalé ce
trou ; l'analyse le conserve, sans zéro imputé. La chauffe de tendance utilise
uniquement les prix. Toute heure manquante dans l'évaluation aurait bloqué le test.

Les **720 opens quotidiens comparables** aux archives horaires existantes
concordent exactement. Aucun prix horaire ancien n'est inventé : le funding
horaire est valorisé approximativement à l'open du jour, et le stress de délai
ancien est d'un **jour**, non d'une heure.

## La tendance lente ne confirme pas son avantage

| Résultat des 60 semaines anciennes | Valeur |
|---|---:|
| Moyenne brute | +62,82 bps/semaine |
| Moyenne nette de base | +46,00 bps/semaine |
| Moyenne nette, coûts stressés | +30,99 bps/semaine |
| Moyenne nette, funding entièrement adverse | +22,23 bps/semaine |
| Moyenne nette, entrée/sortie retardées d'un jour | **−26,64 bps/semaine** |
| Profit factor de base | **1,19** |
| Intervalle bootstrap 98,33 % de la moyenne de base | **[−165,84 ; +251,14] bps** |
| Diagnostic de permutation | p ≈ 0,20 |
| Pire panier hebdomadaire de base | **−17,63 % du notionnel brut** |

ETH apporte +2 769 bps de contribution cumulée pour +2 760 bps de résultat
total ancien : les trois autres actifs, ensemble, n'ajoutent pas de gain net.
Cette concentration, l'intervalle très large et la sensibilité au calendrier
ne justifient pas de construire un bot. Le retard d'un jour mesure la stabilité
calendaire ; il ne représente pas une estimation de la latence réelle du serveur.

Sur les 86 semaines, la moyenne de base reste positive (+48,80 bps), mais
le scénario décalé devient également négatif (−5,48 bps). Le signal brut
positif ne suffit donc pas à franchir les critères enregistrés. Décision :
**`HYPOTHESIS_NOT_CONFIRMED`**. [Résultats complets](long_summary.json).

Ces chiffres décrivent des paniers à notionnel initial fixé, sans stops,
arrondi de taille, contrainte de marge ou superviseur de risque. Les sommes
en bps et le drawdown des paniers clos ne sont pas une courbe de compte réel.
Aucun rendement mensuel, aucune compatibilité avec les caps de risque et
aucun objectif de +30 % ne sont déduits de ce filtre.

## Décision et suite

Suspendre les trois règles étudiées ; ne pas chercher le meilleur paramètre
ou isoler ETH après avoir vu son résultat pour fabriquer un gagnant.
Liquidations payantes et maker à transport inadéquat restent également suspendus.

La prochaine famille à examiner est **le comportement après des chocs de
volume et de volatilité**, avec les OHLCV gratuites conservées : distinguer
continuation et absorption par des règles enregistrées avant calcul. Ce ne
seront pas des liquidations supposées à partir des bougies. La présente passe
ne prétend pas avoir déjà validé cette nouvelle famille.

Le travail utile conservé est une base gratuite plus longue, des hypothèses
réfutées et un moteur de comparaison reproductible. Aucun coût de données
nouveau ; aucune attente de plusieurs mois de collecte.

## Livraison et reproduction

Sélection causale, comptabilité long/short et funding signé/adverse, scénarios
de coûts/délai, contributions, bootstrap et permutations livrés. **193 tests**,
lint/format et typage passent. Les preuves et empreintes figurent dans
[le manifeste](evidence_manifest.json) ; raws et paniers détaillés hors Git.
L'extension a utilisé 96 requêtes publiques de données (quatre prix + 92 funding).

Commandes offline, destinations nouvelles obligatoires :

```bash
rtk proxy uv run python scripts/investigate_free_rotation.py --output tmp/free-rotation-repro
rtk proxy uv run python scripts/investigate_long_trend.py --output tmp/long-trend-repro
```

Les protocoles, ajustements, résultats intermédiaires et défavorables sont
conservés. Aucun ancien dépôt n'est modifié ; seules des briques d'archives
et de validation déjà présentes dans HyperBot2 sont réutilisées.
