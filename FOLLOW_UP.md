# HyperBot2 — suivi de l’implémentation

Date : 7 septembre 2026. Version 0.2.0. Développement, installation et validation
publique bornée sur serveur explicitement demandés. Trading réel interdit.

| Lot | Statut |
|---|---|
| P0 — reprise autonome des composants et tests HyperBot | Livré : package autonome, provenance, 82 tests hérités |
| P1 — métadonnées outcomes, qualification, collector rapide | Outils livrés ; témoin 40 s terminé ; qualification réelle `DATA_BLOCKED` |
| P2 — screening legacy et campagne bornée | Livré : 892 492 lignes relues, runner 18 scénarios ; candidat réel `DATA_BLOCKED` |
| P3 — stratégie, portefeuille, replay/shadow, gates | V0 de simulation livrée et testée ; qualification maker non acquise |
| Exécutable serveur 0.2.0 | Installé séparément dans `/opt/hyperbot2`, Docker non privilégié, healthcheck et arrêt borné |
| Assemblage des données réelles | Capture → fenêtres → moteurs central/pessimiste automatisé ; jointure optionnelle des références datées |
| Validation économique A/OOS et shadow continu | Non acquise |
| Canary et live | Bloqués, non implémentés |

Les anciens services restent arrêtés. Les données legacy ne sont jamais
promues automatiquement en preuves de fills maker.

## Livraison

Voir [README](README.md), [contrats d’entrée](docs/DATA_CONTRACT.md) et
[rapport complet](reports/implementation_2026-09-06/REPORT.md). La configuration
refuse le live. Chaque campagne est bornée et sans relance automatique ; les
répertoires de run existants ne sont pas écrasés. Le nouveau service public est
borné et finalise les artefacts sur SIGTERM/SIGINT. Une interruption brutale est
signalée sans prétendre reprendre son portefeuille. Voir [SERVER.md](docs/SERVER.md).

Le noyau HyperBot est copié : stockage, contrats d’événements, collector,
replay, risque, adaptateurs et recherche. Les modifications ciblées portent
sur `fast=true`, PF par cycle et bootstrap journalier commun aux cryptos.
La comptabilité outcomes et l’interface de campagne sont nouvelles.

## Prochaine décision fondée sur les données

Diagnostic borné terminé : **NO-GO maker HIP-4 avec le flux public et les règles
actuels**. Voir [mesures et décision](reports/feasibility_2026-09-06/REPORT.md).
Sur le serveur : 0/896 carnets admissibles avec placement 350 + incertitude
50 ms ; couverture temporelle fraîche de 17,8 % ; 0/36 fenêtres complètes
qualifiables pendant toute l’exposition. Les 350 ms sont une hypothèse héritée,
pas une mesure d’ordre. Frais/spécification, référence causale et file restent
non qualifiés. Aucune conclusion de rentabilité ne peut être publiée.

Ne pas lancer de collecte permanente. Un accès L4 HIP-4 est documenté chez
QuickNode, mais non testé ; la prochaine étape éventuelle est un test borné sur
un outcome YES/NO, conditionné à cet accès et à son budget. Aucun abonnement
souscrit, aucun ordre ni service relancé. Diagnostic offline reproductible livré,
152 tests passent ; runtime et release serveur inchangés.
Les bornes de risque, l’abstention et les gates de la fondation restent inchangés.

## Validation serveur

Release courante : `b44a0baa421ac7f2`, paquet 0.2.0. Le serveur a confirmé un
healthcheck positif et 16 abonnements publics. Les tests couvrent maintenant
les erreurs disque, le verrou d’instance, l’absence de données, la jointure
causale et l’arrêt opérateur. Une course détectée lors du premier test SIGTERM
a été corrigée avant la release courante. Les erreurs du premier essai sont
conservées dans son run séparé ; elles ne sont pas maquillées en succès.

149 tests locaux passent ; lint, typage strict, build et installation serveur
vérifiés. Les preuves finales et le statut après validation sont conservés dans
[le rapport serveur](reports/server_2026-09-06/REPORT.md).

## Recherche étendue après demande de poursuivre jusqu’à un GO

Vague du 6 septembre terminée, **aucun GO économique obtenu**. Protocole
enregistré, 180 jours complets OHLC/funding sur BTC/ETH/SOL/HYPE récupérés,
48 simulations de deux variantes taker sans optimisation, 22 paniers examinés.
Breakout/retour à moyenne rejetés après les trois blocs de test ; funding
insuffisant pour la cible dans le benchmark fixé ; aucun panier favorable.
Voir [résultats et limites](reports/search_2026-09-06/REPORT.md).

Piste suivante : L4 HIP-4 0xArchive, compte gratuit limité documenté et couverture
des marchés annoncée par son catalogue public. Accès testé : HTTP 401 sans clé.
L’utilisateur confirme ne connaître aucun accès L4. Reconstructeur immuable,
sonde bornée et wrapper serveur livrés séparément ; [procédure](docs/L4_RESEARCH.md).
Déclencheur manquant : clé de données 0xArchive stockée hors Git. Aucun achat,
ordre ou relance des services ; gates inchangées. 163 tests, lint et types passent.
Les fenêtres historiques réservées de cette vague sont désormais consommées.

## Accès 0xArchive et diagnostic L4 du 7 septembre

Le prérequis de clé ci-dessus est résolu : clé fournie dans `keys.txt`, ignorée
par Git, permissions 0600, installation protégée sur le serveur. Authentification
REST et WebSocket fonctionnelles. Aucun abonnement supplémentaire souscrit.

**Reconstruction historique validée sur l’échantillon ; aucun GO économique.**
Huit carnets YES/NO BTC/ETH/SOL/HYPE reconstruits exactement sur une minute
(369 diffs). La profondeur YES fusionnée avec le complément NO reproduit les
prix, tailles et nombres d’ordres de trois captures natives Hyperliquid.
Cette preuve reste de classe B pour les historiques ; elle ne qualifie pas les
fills maker ni la priorité entre les deux carnets.

Deux témoins serveur de 30 s testent `hip4_l4_diffs` puis `hip4_l4_orders` :
âges médians 541/585 ms ; aucun des 156/269 événements sous les 100 ms
disponibles avant placement selon l’hypothèse 350 + 50 ms. Pas de séquence
`seq` observée dans les diffs WebSocket ; continuité complète non démontrée.
Le statut d’exécution reste `DATA_BLOCKED`, les gates inchangées.

Livrés : lecture sûre de la clé nommée, témoin L4 borné avec horloges de
réception et stockage HyperBot réutilisé, fusion de profondeur duale et audit
offline reproductible. 167 tests passent, lint/format et types vérifiés.
Les outils de recherche sont installés séparément ; runtime courant inchangé,
anciens bots arrêtés, aucune collecte permanente. Voir le
[rapport L4 et la prochaine piste bornée](reports/l4_2026-09-07/REPORT.md).

## Diagnostic maker final — terminé le 7 septembre

**NO-GO du candidat maker HIP-4 avec le transport et les hypothèses actuels.**
La comparaison simultanée serveur est terminée : BTC puis ETH, 60 s chacun,
444 carnets natifs et 168 événements L4. Aucun carnet natif admissible à
100 ms ; 0/432 fenêtres natives fraîches pendant les 1 350 ms d’exposition
hypothétique. Les fenêtres se chevauchent, sans interprétation statistique
d’essais indépendants. Les limites et gates restent inchangées.

Un raccord snapshot WebSocket/diffs incomplet est confirmé par REST. Après
réparation strictement historique par checkpoint REST : 183/183 comparaisons
de profondeur concordantes et 6/6 checkpoints REST concordants. Cela prouve
la cohérence des données historiques, sans restaurer une réception causale
passée ni qualifier les fills. L’absence de seq seule n’est pas un gap.

Capture simultanée, fermeture conservatrice des blocs et analyse offline
livrées et installées séparément. 174 tests, lint/format et types passent.
Les bots restent arrêtés. **Suspendre cette piste maker** ; réouverture
conditionnée à une amélioration démontrée du transport ou à une nouvelle
conception validée, sans assouplir les gates pour forcer un résultat.
Voir [la décision finale et les preuves](reports/maker_final_2026-09-07/REPORT.md).
