# Rapport or/argent : faible profit, edge insuffisant

**Pas de GO.** La règle centrale à 1x gagne 53,96 $ sur 206 jours hors
infrastructure, avec 6,04 % de drawdown horaire. Les mois rouges sont acceptés
et le résultat cumulé est positif. Mais le gain devient presque nul sous
coûts renforcés, négatif avec une heure de retard, et son incertitude inclut
zéro. Ce résultat ne justifie pas de développer un bot dédié.

## Hypothèse testée

[Protocole figé](PROTOCOL.md) : log du ratio GOLD/SILVER, moyenne et sigma sur
240 heures antérieures excluant la bougie signal. Entrer entre deux et quatre
sigmas, vendre le métal relativement cher et acheter l'autre, notionals égaux
avant arrondis. Moyenne/sigma figés à l'entrée ; sortie au retour à 0,5 sigma,
à quatre sigmas adverses ou après 72 heures. Délai de 24 heures après sortie.

Capital initial 1 000 $, sizing à l'equity courante, plafonds bruts 0,5x/1x/1,5x.
Arrêt sur perte observée de la paire de 3 % du capital d'entrée ; arrêt global
à 20 % depuis le sommet. Sorties au prochain open avec slippage : dépassements
conservés. Les limites s'appliquent aux simulations, aucune configuration live
n'est modifiée. Une couverture en dollars ne garantit pas la convergence du
rapport or/argent.

Données natives existantes, 4 944 heures du 12 février au 6 septembre 2026
exclusif, sans acquisition supplémentaire. Les prix ont déjà servi au test
de tendance : pas d'échantillon globalement vierge. Frais du snapshot natif,
GOLD 9 bps/SILVER 0,9 bp par côté, slippage central 2 bps et funding signé des
positions détenues. [Barème trade.xyz](https://docs.trade.xyz/perp-mechanics/fees.md).
L'historique exhaustif des frais et l'exécution réelle restent non qualifiés.

## Résultats complets, sans coût d'infrastructure supplémentaire

| Plafond brut | Central | Coûts renforcés | Retard 1 h | Funding adverse | Sans aucun coût |
|---|---:|---:|---:|---:|---:|
| 0,5x | +27,30 $ | +1,60 $ | −1,36 $ | +17,72 $ | +51,08 $ |
| 1x | +53,96 $ | +1,73 $ | −4,00 $ | +34,39 $ | +103,14 $ |
| 1,5x | −31,52 $ | −102,85 $ | −104,27 $ | −57,33 $ | +30,08 $ |

Chaque ligne est une simulation séparée avec 32 trades. La hausse à 1,5x
déclenche trois arrêts sur perte de paire en central, et modifie donc les
sorties et la chronologie. Ce n'est pas une multiplication linéaire du PnL 1x.
Ce résultat dépend de la règle de risque enregistrée ; il ne démontre pas que
toute augmentation de risque serait nécessairement perdante.

À 1x central : quatorze sorties sur convergence, douze sur durée, six sur stop
du ratio ; cinq périodes calendaires positives, deux négatives et une neutre.
Février et septembre sont partiels. Les six mois complets mars–août comprennent
cinq mois gagnants et juin perdant. Ces données ne valident pas douze mois.

Le rendement composé équivalent est **+0,77 % par mois**, hors infra ; le gain
linéaire sur 30 jours est environ **7,86 $**, très éloigné de 150–200 $. Avec
20 $/30 jours débités dans le portefeuille, le total 1x central devient
**−88,02 $**. Le coût est hypothétique, aucune dépense réelle n'est engagée.

## Risque et incertitude

À 1x central sans infra : drawdown horaire **6,04 %**, enveloppe OHLC adverse
**7,29 %**, maximum environ **41,21 jours** sous le précédent sommet. Les mois
rouges ne sont donc pas le motif de rejet. Avec 1,5x, retard et infra, le
drawdown horaire monte à **26,47 %**, supérieur au plafond accepté ; il est
conservé et ne devient pas artificiellement 20 % par arrêt de la courbe.

Le [diagnostic complémentaire](VALIDATION_NOTE.md) utilise les rendements
quotidiens de l'equity, positions ouvertes comprises, et des blocs mobiles
de quatorze jours. IC descriptifs 95 % de l'équivalent mensuel à 1x :

| Scénario | IC descriptif mensuel |
|---|---:|
| Central | [−0,87 % ; +2,48 %] |
| Coûts renforcés | [−1,63 % ; +1,67 %] |
| Retard | [−1,97 % ; +1,76 %] |
| Funding adverse | [−1,18 % ; +2,21 %] |

Tous contiennent zéro. Ce diagnostic intervient après identification des
petits résultats positifs : il n'est ni confirmatoire ni corrigé de toutes
les recherches antérieures. Les fractions de tirages positifs du fichier
d'audit ne sont pas des probabilités que la stratégie soit rentable à l'avenir.

Les courbes horaires incluent latent, cash, frais et funding. Les extrêmes OHLC
des deux actifs forment une enveloppe hypothétique indépendante, pas un chemin
observé simultanément. Les gaps, tailles minimales et arrondis sont traités,
mais les bougies ne prouvent ni profondeur ni mark natif ni liquidation réelle.

## Décision et livraison

Le filtre mécanique initial retient 0,5x et 1x sans infra comme résultats
positifs à examiner ; c'est le sens de `RESEARCH_CANDIDATE_UNQUALIFIED` dans
le résumé brut. Après examen économique, retard et incertitude : **aucun edge
assez intéressant pour le bot**, règle suspendue. Ne pas transformer ce
marqueur préliminaire en GO ni supprimer le stop après coup pour sauver 1,5x.

239 tests passent ; lint/format 210 fichiers et mypy 61 sources passent.
Les tests couvrent causalité des statistiques, couverture en dollars, signes
du funding, cash réconcilié, gaps après seuil et absence de réentrée après
arrêt. Trente-deux artefacts du test et l'audit sont reproduits exactement :
[preuve](reproduction.json). Aucun achat, ordre ou modification serveur.

Recherche globale active. La prochaine qualification peut porter sur WTI/Brent,
avec deux marchés à frais réduits, en vérifiant au préalable leurs différences
de contrats/oracles et leur historique natif disponible. Ce sera une nouvelle
hypothèse, pas une substitution de ticker présentée comme validation de celle-ci.
