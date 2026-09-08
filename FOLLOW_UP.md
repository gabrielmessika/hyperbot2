# HyperBot2 — suivi de l’implémentation

Date : 7 septembre 2026. Version 0.2.0. Développement, installation et validation
publique bornée sur serveur explicitement demandés. Trading réel interdit.

**Recherche bloquée en attente de cadrage des ressources.** Après la remarque
utilisateur sur environ 9 h 30 et la consommation excessive, une limite ferme
de temps ou de tokens a été demandée. La même décision reste en attente pendant
trois reprises consécutives ; aucun plafond n'a été fourni. Les deux premières
reprises n'ont produit aucun nouveau résultat économique. Ne pas assimiler
les relances automatiques de l'objectif à une réponse au plafond demandé.
L'objectif économique demeure non atteint ; le blocage concerne la poursuite
responsable de la consommation, pas une impossibilité démontrée du trading.
Les calculs publiés sont terminés. Aucune nouvelle expérience en cours.

**Dernière décision : bilan demandé après environ 9 h 30 de recherche. Aucun
edge validé. Nouvelle étude de choc collectif suspendue avant calcul ; les
anciennes mentions « prochaine piste » ne constituent pas une relance acquise.**
Voir le [bilan économique et de ressources](reports/RESEARCH_REVIEW_2026-09-07.md).

Sonde complémentaire bornée, sans backtest : deux appels publics confirment
2 190 bougies ARB 4 h couvrant 2025 et les 48 fundings horaires demandés au
début de l'année. Les autres actifs et le funding annuel restent non qualifiés.
[Preuve de disponibilité native](reports/native_2025_qualification_2026-09-07/REPORT.md).
Cette information peut permettre une épreuve native d'une règle lente existante ;
elle ne constitue pas un edge et ne relance pas l'étude de choc suspendue.

Extension de qualification terminée, dix appels supplémentaires : neuf actifs
couvrent 2025, XMR/ZEC échouent (trous et volumes nuls). 38 des 47 anciens paniers
acheteurs Binance ne passent pas même le contrôle des bougies natives pendant
leur détention. Collecte annuelle de funding non engagée ; aucun nouveau PnL.
Les résultats de transfert restent conservés et ne deviennent pas natifs.

Contrôle natif ciblé terminé sur les neuf actifs disponibles, règle acheteuse
inchangée : 47 paniers 2025 donnent −108,45 bps après frais/slippage avant
funding, contre +130,94 bps sur 23 paniers 2026. Le plafond 2025 est négatif
également sous coûts renforcés et retard 4 h ; le funding adverse ne peut pas
le rendre positif. Pas de collecte annuelle de funding ni de portefeuille.
[Résultat natif](reports/native_price_ceiling_2026-09-07/REPORT.md).
Huit artefacts reproduits, 23 classements horaires identiques, 1 890 contrôles
de comptabilité de prix ; huit tests ciblés passent. Aucun appel réseau nouveau.

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

## Investigation BTC/ETH — terminée le 7 septembre

Hypothèse de retour de l’écart relatif sur quelques heures testée selon un
protocole enregistré, avec les 180 jours existants. 30 jours de chauffe puis
150 jours exploratoires ; données déjà consultées, aucun nouveau bloc OOS.
Modèle log-prix estimé sur le passé et gelé pendant chaque événement/position.

**`HYPOTHESIS_NOT_CONFIRMED`** : 33 événements ; à six heures, écart réduit
dans 60,6 % des cas mais rendement moyen de paire −5,47 bps avant coûts et
−18,48 bps après frais/slippage, avant funding. Intervalle bootstrap 95 %
[−56,60 ; +4,15] bps : aucun avantage positif démontré.

Simulation de base : −3,62 $ de trading sur cinq blocs de 30 jours, −103,62 $
après infrastructure, PF 0,58. Contrôle zéro coûts de trading : +0,62 $ avant
infrastructure. Aucun réglage postérieur aux résultats ni levier ajouté.
Pas de développement d’un bot live sur cette règle ou de validation prospective
justifiée par ces résultats. Voir [le rapport](reports/pairs_2026-09-07/REPORT.md).

Réutilisation du lecteur d’archives ; features et simulateur offline livrés,
modèle sans fuite future et comptabilité à deux jambes testés. 178 tests,
lint/format et mypy passent. Une requête publique de métadonnées, aucune clé
utilisée, aucun serveur ou service modifié. Les raws restent hors Git.

## Investigation des rebonds après liquidations — 7 septembre

**`INSUFFICIENT_SAMPLE`**, aucun GO. Accès 0xArchive liquidations/OI BTC/ETH
fonctionnel ; campagne 180 jours arrêtée au premier HTTP 403, abonnement
limité aux 30 derniers jours. Pilote distinct enregistré avant téléchargement
et calcul : 28 jours, sept jours de chauffe, prix/funding existants réutilisés.

Un événement BTC, aucun ETH admissible, aucun témoin apparié. Épisode du
28 août 16:00 UTC : 18,46 M$ liquidés longs, 2 565 lignes brutes sur trois
pages, volumes/nombres réconciliés. Horizon principal six heures : −3,09 bps
brut, −16,77 bps net de coûts de base/funding conservateur ; coûts stressés
−31,76 bps. Échantillon trop faible pour confirmer ou rejeter le mécanisme ;
pas de bootstrap donnant une fausse précision et pas de rendement mensuel estimé.

Absences de buckets non imputées à zéro ; couverture des liquidations non
certifiée et identités liquidateur/liquidé suspectes, non utilisées. Prochaine
étape : profondeur 90–180 jours et audit de couverture avant nouveau test,
pas un bot live ni un changement opportuniste de seuils. Voir
[protocole, résultats, provenance et limites](reports/liquidations_2026-09-07/REPORT.md).

Client borné, parseur, sélection et analyse offline réutilisables ; 184 tests,
lint/format et mypy passent. 16 requêtes, 1,70 Mo, aucun achat. Aucun serveur,
service ou configuration live modifié ; aucun ancien bot relancé.

## Recherche d'archives longues de liquidations — 7 septembre

Recherche des sources locales/serveur, archive native S3, CSV officiel GitHub,
HypeDexer, ByKaranteli, PurrData et catalogue 0xArchive terminée pour cette passe.
Aucun accès gratuit autonome à 90–180 jours qualifié : S3 anonyme HTTP 403,
CSV GitHub de 2023 sans coin/sens, HypeDexer API HTTP 401 et export avec CAPTCHA,
autres sources hors couverture ou en attente de lancement. Inventaires de noms
et schémas, sans prétendre avoir scanné exhaustivement chaque ancien raw.

Progrès de qualité : **3/3 liquidations échantillonnées confirmées nativement**
par `userFillsByTime`, identifiants, propriété `liquidation`, méthode `market`,
compte liquidé et montants numériques concordants. Couverture et identité du
liquidateur non validées. Le statut économique reste `INSUFFICIENT_SAMPLE`.

Paquet prêt pour BTC/ETH du 10 mars au 6 septembre UTC exclusif : export
liquidations + OI, minimum publié théorique 30 $ (devis réel non obtenu), ou
Build API 49 $ mensuels avec historique complet annoncé. Alternative gratuite
HypeDexer à vérifier sur un jour via CAPTCHA humain avant tout volume massif.
Aucun achat ni commande d'export créé ; aucun rendement supplémentaire calculé.
Voir [sources, preuves et modalités de reprise](reports/liquidation_history_2026-09-07/REPORT.md).

Audit natif offline et tests livrés ; 187 tests, lint/format et mypy passent.
Serveur consulté en lecture seule, aucun service ou paramètre live modifié.

## Recherche recentrée sur les données gratuites — 7 septembre

Instruction utilisateur persistée dans `AGENTS.md` : **aucune nouvelle dépense**,
explorer des mécanismes différents et suspendre les voies exigeant un accès
payant. Les propositions d'achat précédentes sont abandonnées. Liquidations
et maker restent suspendus, sans relance de bot ou modification serveur.

Trois nouvelles règles testées avec les archives gratuites existantes, sans
réglage après résultats : force relative 7 j (149 paniers, +4,87 bps nets mais
−10,18 bps en coûts stressés), portage relatif (147 paniers, −12,71 bps nets),
tendance 30 j / détention 7 j (21 paniers positifs, approfondissement nécessaire).

Extension **gratuite effectuée dans la même passe** : 640 jours communs de
prix quotidiens BTC/ETH/SOL/HYPE et funding horaire, 96 requêtes publiques.
HYPE commence quatre jours après la date demandée ; intersection de couverture
enregistrée avant calcul ancien. Dix heures de funding HYPE absentes au début
de chauffe, hors positions, conservées comme absentes sans imputation. 720
opens quotidiens concordent avec les archives horaires déjà présentes.

60 semaines anciennes supplémentaires : tendance +46,00 bps nets/semaine,
PF 1,19, intervalle 98,33 % [−165,84 ; +251,14], retard d'un jour −26,64 bps ;
gains concentrés sur ETH. **`HYPOTHESIS_NOT_CONFIRMED`**, règle suspendue avec
les deux autres. Aucun rendement de portefeuille réel ou mensuel extrapolé.

Prochaine famille : chocs de volume/volatilité sur les OHLCV gratuites, avec
nouveau protocole avant calcul, pas reparamétrage des règles rejetées.
Voir [résultats, données et reproduction](reports/free_rotation_2026-09-07/REPORT.md).
Moteur offline et tests livrés : 193 tests, lint/format et types passent.

## Recherche gratuite poursuivie : volume, écarts et flux — 7 septembre

Six règles supplémentaires enregistrées puis calculées, aucun achat et aucun
trading. Volume natif : continuation 211 événements, −1,91 bps nets à 6 h ;
rejet par mèche 146 événements, −11,53 bps. Famille suspendue.
Voir [rapport volume](reports/volume_shocks_2026-09-07/REPORT.md).

Nouvelle source gratuite réutilisable : 21 GET publics Binance, 12 960 bougies
horaires BTC/ETH/SOL USDC et 1 620 paiements de funding, six mois complets.
Écart HL/Binance et différentiel de funding : aucun déclenchement aux seuils
économiques enregistrés. Les écarts de clôture à la médiane 7 j culminent à
11,27/13,32/14,53 bps, avant frais des deux jambes. Timestamps de funding Binance
avec offsets 0–26 ms contrôlés et conservés pour l'attribution des paiements.
Voir [rapport interplateformes](reports/cross_venue_2026-09-07/REPORT.md).

Flux agressif Binance comme signal HL : absorption négative (14 événements),
pression acceptée positive (109 événements, +17,05 bps nets, PF 1,42,
stress coûts +2,05 bps, retard +11,83). Mais IC 97,5 % [−6,67 ; +42,77], gains
concentrés sur ETH, marge économique faible avec 1 000 $. Gate échouée,
`HYPOTHESIS_NOT_CONFIRMED`, aucune promotion. Voir
[rapport flux](reports/order_flow_2026-09-07/REPORT.md).

Recherche toujours active : explorer gratuitement les fundings d'un univers
élargi pour chercher une marge plus grande ; ne pas relever le levier pour
compenser le faible edge des règles précédentes. Aucun service/live modifié.

Filtre effectué sur 20 coins core supplémentaires (39 requêtes gratuites,
19 historiques funding complets /20) : CASHCAT seul dépasse le seuil proxy
30 $/mois pour 500 $ de short (+35,29 $ avant hedge/coûts). Spot KuCoin confirmé,
prix/funding/FX gratuits acquis et simulation à quantités égales effectuée.
La version statique 500 $ spot /500 $ marge viole le stress de maintenance 20 %
dans l'ancien segment le 5 août et dans le mois sélectionné le 24 août,
y compris sans frais. Aucun profit crédité au-delà de ces violations.
`HEDGE_ECONOMICS_NOT_CONFIRMED` ; voir
[filtre et hedge CASHCAT](reports/wide_funding_2026-09-07/REPORT.md).

## Actions HIP-3 : week-ends et nuits — recherche poursuivie le 7 septembre

Nouvel historique gratuit : 206 jours horaires/funding sur sept actions xyz
(TSLA/NVDA/HOOD/META/AMZN puis COIN/MSTR), 77 requêtes natives. Pas de reprise
des paramètres directionnels BOT05. Calendrier New York/fériés/DST testé.

Fade week-end : +118,47 bps nets sur 19 événements/11 week-ends, mais concentration
HOOD et gates de stabilité/échantillon échouées. Réplication enregistrée COIN/MSTR,
sans retoucher la règle : +66,04 bps sur 25 événements/15 week-ends, mais retard
1 h −4,69 bps. Pas de GO. Fréquence trop faible dans l'illustration sans levier
pour couvrir le budget hypothétique de 20 $/mois à 1 000 $ de capital.
Voir [rapport et réplication](reports/weekend_repricing_2026-09-07/REPORT.md).

Hypothèse distincte nocturne mardi–vendredi, avec ancien/validation séparés :
fade −52,46/−53,14 bps ; follow +8,55/+9,16 mais stress −15,39/−14,83 et intervalles
contenant zéro. 174 puis 170 événements, aucune optimisation entre segments.
Voir [rapport nocturne](reports/overnight_repricing_2026-09-07/REPORT.md).

La recherche reste active, aucun edge économiquement et statistiquement
qualifié. Prochain lot à cadrer : vérifier si les archives outcomes existantes
permettent de tester une erreur de prix côté taker à partir des probabilités de
résolution, en réutilisant le moteur existant ; suspendre si la donnée gratuite
ne permet pas un diagnostic valable. Aucun achat ni bot relancé.

Vérification de livraison : **213 tests**, lint/format et mypy sur 53 fichiers
source passent. Dix artefacts volume/écarts/flux/hedge puis dix artefacts
week-end/réplication/nocturne reproduits exactement par SHA-256. Livraison
offline uniquement ; aucune configuration serveur, collecte active ou gateway
de trading modifiée. Les nouveaux raw publics restent ignorés Git.

## Outcomes taker : archives et résolutions officielles — 7 septembre

115 contrats retrouvés dans 892 492 observations Nautilus existantes : BTC 40,
ETH/SOL/HYPE 25 chacun. Extraction déterministe de 642 carnets avec horloges
événement/réception, environ 512 ko avec manifestes. 113 résolutions officielles
obtenues gratuitement par `settledOutcome`, identités toutes réconciliées.
Les 99 résultats paper legacy ne sont pas utilisés comme labels officiels.

Règle enregistrée : décision quotidienne, benchmark digital et volatilité
prudente, achat à l'ask puis résolution, sizing ~10 $ sans levier. Deux contrats
sondés avant enregistrement exclus. Sur 226 côtés : 16 manquants/vides, 12 hors
plage de prix, 198 frais mais marge insuffisante. Meilleure marge prudente
2,58 points contre 5 requis, **aucun signal**. Aucun PnL tradé ni preuve de
rentabilité ; `HYPOTHESIS_NOT_CONFIRMED`, règle suspendue sans abaisser le seuil.
Voir [rapport outcomes taker](reports/outcome_taker_2026-09-07/REPORT.md).

216 tests, lint/format et mypy 54 sources passent. Carnets/univers et résultats
reproduits exactement, quatre artefacts contrôlés. Livraison recherche offline,
aucun achat, aucun changement serveur/live. Recherche toujours active.

Prochain lot : diagnostic des flux BTC/ETH/HYPE déjà collectés en août pour une
hypothèse taker de microstructure (flux agressif et déséquilibre de carnet).
Vérifier la causalité et les coûts, puis figer une règle avant les résultats.
Ne pas recommencer une collecte d'un mois ni acheter de données par défaut.

## Microstructure taker : pilote et réplication — 7 septembre

336 segments Hyperbot existants, 44,20 millions de lignes parcourues,
11,73 millions d'événements BTC/ETH/HYPE extraits avec horloges natives et
réception, aucune nouvelle acquisition. Règles figées continuation/absorption,
pilote 16–17 août puis réplication 25–27 août. Déduplication coin/time/tid
précisée d'après la documentation native avant calcul économique.

À 5 minutes : continuation −10,11 bps nets pilote (120 événements évaluables)
puis −10,85 réplication (294) ; absorption −11,61 (167) puis −10,06 (272).
Stress, retard et horizon descriptif 30 min négatifs. Chaque jour et actif
négatif. Couverture fills simulés seulement 69,9–74,6 %, pas de portefeuille
complet ni de GO. Famille suspendue. Voir
[rapport microstructure](reports/microstructure_2026-09-07/REPORT.md).

221 tests, lint/format 174 fichiers et mypy 55 sources passent. Réextraction
déterministe du 16 août et évaluations reproduites par checksum. Livraison
offline ; aucun achat, changement serveur ou bot relancé. Recherche active.

Priorité suivante issue d'un constat : auditer les frais des expériences
actions HIP-3. Le snapshot natif indique growth mode sur six des sept marchés,
soit tarif actuel 0,9 bp taker au lieu des 9 bps standards utilisés ; MSTR reste
standard. Ne pas changer les signaux. Vérifier gratuitement l'historique du
mode, ou identifier explicitement une sensibilité aux frais actuels ; ne pas
confondre état courant et factures historiques. Voir
[note préalable](reports/hip3_fee_review_2026-09-07/NOTE.md).

Décision utilisateur du 7 septembre : **+15 % ou +20 % nets mensuels sont aussi
acceptables**, soit 150–200 $ sur 1 000 $. L'objectif initial +30 % n'est donc
plus un minimum impératif. Cela assouplit la cible de performance, pas les
gates hors échantillon, coûts, capacité, risque et absence de trading live.
Les seuils de pré-recherche à 30 $/mois restent de simples filtres pour décider
d'une validation supplémentaire ; ils ne prouvent pas l'atteinte de cette cible.

## Audit des frais HIP-3 terminé — 7 septembre

Tarif growth 0,9 bp confirmé sur six actifs, MSTR 9 bps ; activation trade.xyz
corroborée par l'annonce officielle du 24 novembre 2025. Timeline exhaustive
par marché non attestée : sensibilité au tarif observé explicitement qualifiée.
Signaux et exécution inchangés, 5 256 comparaisons contre recalcul brut réussies.

Follow nocturne désormais +21,28/+21,84 bps nets ancien/validation, stress
+10,07/+10,53, mais IC incluant zéro. Allocation 1 000 $ TOTAL répartie entre
signaux simultanés : seulement +60,18 $/109 j puis +11,88 $/97 j avant infra.
Week-end fade positif mais rare, économie insuffisante. Aucun GO, aucun achat.
Voir [rapport frais](reports/hip3_fee_review_2026-09-07/REPORT.md).

224 tests, lint/format 180 fichiers et mypy 56 sources passent. Sept artefacts
reproduits exactement. Anciennes baselines préservées, livraison offline.

Prochain lot : observations proches de l'expiration outcomes retrouvées dans
les deux fichiers legacy `short_expiry_features.csv` (110 contrats /41 dates,
sources largement chevauchantes, ne pas doubler l'effectif). Vérifier fraîcheur
des références, profondeur et labels natifs ; établir d'abord une borne de
revenu pour écarter une économie trop faible. Aucune importation des paramètres
ou conclusions directionnelles TRIDENT, aucun GO fondé sur une borne optimiste.

## Fin d'échéance : borne et références auditées — 7 septembre

115 contrats /40 dates, enveloppe 41 jours. Achat du gagnant connu à l'avance,
prix à cinq minutes, 10 % du meilleur ask : borne 276,05 $ sur la période,
181,99 $/30 j après hypothèses de retenue 7 bps et infra 20 $. **Ce n'est pas
un rendement de stratégie.** Un seul SOL NO à 0,433 fournit 62,77 % du gain ;
sans lui, même cette borne devient 55,19 $/30 j. Seulement 25 asks gagnants
utilisables à l'instant fixe. La borne plus lâche dépasse largement la cible :
elle ne permet pas de rejeter globalement, ni d'accorder un GO.

Audit causal : `seconds_left` legacy antérieur de ~23 s à la journalisation ;
10 lignes mainnet et 13 paper arrivent à/après échéance. Ne jamais antidater
les références au début de boucle. 42/115 contrats avec références journalisées
avant la décision ; timestamps source OKX disponibles pour 42, Coinbase frais
pour 41, mais absents côté Hyperliquid. Logs conditionnés par les opportunités
legacy : sélection non aléatoire, pas de référence native pleinement qualifiée.
Voir [rapport fin d'échéance](reports/expiry_bound_2026-09-07/REPORT.md).

230 tests, lint/format 186 fichiers, mypy 57 sources passent. Cinq artefacts
finaux reproduits exactement. Livraison offline, raw préservés, aucun achat,
configuration serveur ou service modifié. Recherche active, aucun edge GO.
Prochaine qualification bornée : références disponibles avant décision et
incertitude de prix natif ; suspendre si elles ne permettent pas un test causal
avec les données gratuites. Toute nouvelle règle sur ces résultats déjà vus
reste exploratoire jusqu'à réplication indépendante.

## Signal fin d'échéance testé et suspendu — 7 septembre

Référence OKX SPOT USDT qualifiée avant décision sur 31 contrats : 18 BTC,
7 ETH, 6 SOL. Onze HYPE sans référence adéquate en devise, 73 contrats sans
référence sélectionnée. Benchmark existant à cinq minutes, trois volatilités,
prix ±15 bps (hypothèse, pas borne garantie du basis), haircut et marge inchangés.
Parmi 62 côtés : 17 carnets absents/invalides/stale, 39 asks hors plage,
six marges insuffisantes. Meilleure marge −18,54 points contre +5 requis.
**Zéro signal**, aucun PnL de transactions ; pas d'optimisation pour sauver
la variante. Labels déjà vus, biais de sélection legacy, aucune preuve OOS.
Voir [rapport signal fin d'échéance](reports/expiry_signal_2026-09-07/REPORT.md).

231 tests, lint/format 191 fichiers et mypy 58 sources passent. Trois artefacts
reproduits exactement. Aucun achat, ordre, changement serveur ou service.
Recherche active ; cette règle est suspendue. Prochaine voie distincte à
enregistrer avant calcul : actions crypto HIP-3 COIN/MSTR couvertes par BTC,
écart relatif après hedge, funding et frais par jambe. Historiques natifs
existants suffisants pour commencer sans nouvelle collecte ou abonnement.

## COIN/MSTR couverts par BTC : règle rejetée — 7 septembre

Régression sur 20 séances antérieures, résidu intraday à 14 h NY, fade et
continuation préenregistrés, sortie lendemain hors week-end/jours fériés.
180 jours natifs existants ; 15 signaux action, 13 paniers après sélection
du plus grand écart (trois COIN, dix MSTR). 1 000 $ de notional TOTAL partagé
entre les jambes par beta ; frais/funding/slippage des deux jambes inclus.

Fade −7,62 bps/panier central, −23,30 stress, −13,99 retard ; continuation
−19,75, −35,43, −13,37. PnL proxies −9,90/−25,68 $ sur 180 j. Même sans coût,
fade seulement +7,78 $. Ancien/récent neuf/quatre trades et inversion des signes,
IC 97,5 % contenant zéro. Aucun gate ne passe ; pas de sélection a posteriori
de COIN seul. Pire trade fade −36,05 $ : risque intraday non validé par ce
filtre économique sans stops. Voir
[rapport hedge actions crypto](reports/crypto_equity_hedge_2026-09-07/REPORT.md).

233 tests, deux tests ciblés relancés après clarification Decimal ; lint/format
196 fichiers et mypy 59 sources passent. Quatre artefacts finaux reproduits.
Aucun achat, ordre, modification serveur ou service. Recherche active, règles
suspendues. Prochain lot à qualifier : historique natif gratuit des métaux/
énergie HIP-3 à frais réduits pour une hypothèse de tendance distincte ; ne pas
recaler la régression rejetée sur ces treize trades.

## Tolérance aux mois rouges — décision utilisateur du 7 septembre

L'utilisateur accepte davantage de risque dans les recherches et des mois/
séances rouges (exemple huit mois positifs sur douze), sous réserve d'un résultat
global largement positif. Les prochains tests doivent juger gain cumulé net,
drawdown, pertes extrêmes et récupération ; ne plus utiliser un mois ou segment
rouge comme veto isolé. Objectif mensuel acceptable 15–20 %, sans minimum garanti
chaque mois. Voir [politique de recherche risque](reports/RISK_RESEARCH_POLICY_2026-09-07.md).

Réponse utilisateur reçue : **20 % de drawdown maximal depuis le sommet du
capital**, environ 200 $ pour un sommet de 1 000 $. Mesurer la courbe avec
positions ouvertes et coûts ; les seules sorties ne valident pas ce plafond.
Comparaisons possibles en simulation, limites runtime/live inchangées. Conserver
les anciennes baselines et étiqueter les réévaluations. La dernière règle hedge
reste rejetée car son total net est négatif, indépendamment des mois rouges.

## Tendance métaux/énergie testée avec risque accru — 7 septembre

GOLD/SILVER/CL, 206 jours horaires natifs complets, 33 requêtes gratuites /
3,44 Mo. Protocole avant acquisition : breakout 240 h, trailing 3 ATR24,
durée sept jours. Plafonds bruts 0,5x/1x/1,5x, sizing au risque, equity composée,
arrondis natifs ; courbes horaires incluant latent, funding, frais et infra.

Tous les totaux négatifs, même sans coût. Central sans infra : −22,95/−52,59/
−56,61 $ avec 94 trades ; stress −41,29/−86,80/−103,60 $. DD horaires centraux
6,01/10,21/11,83 % ; quatre périodes vertes/quatre rouges dont deux partielles.
Rejet dû au total net négatif, pas aux mois rouges. Certaines sensibilités
avec infra dépassent 20 % malgré arrêt, jusqu'à 25,78 % ; dépassements conservés.
Voir [rapport tendance commodities](reports/commodity_trend_2026-09-07/REPORT.md).

236 tests, lint/format 203 fichiers et mypy 60 sources passent. Trente-deux
artefacts finaux reproduits. Aucun coût de données, ordre ou changement serveur.
Recherche active, règle suspendue. Prochaine piste à enregistrer : écart relatif
or/argent couvert avec le même historique gratuit ; période désormais consultée,
donc toute découverte devra être répliquée ailleurs sans optimisation a posteriori.

## Rapport or/argent : petit profit non retenu — 7 septembre

Ratio log GOLD/SILVER, modèle 240 h antérieures figé à l'entrée, seuils 2/0,5/4,
durée 72 h ; notions égales, risque de paire 3 % et drawdown global 20 % observés
avec sortie au prochain open. Réutilisation intégrale des 206 jours gratuits.

32 trades à 1x : +53,96 $ central sans infra (+0,77 % mensuel composé), mais
+1,73 $ seulement avec coûts renforcés, −4,00 $ avec retard, +34,39 $ funding
adverse. DD horaire 6,04 %, enveloppe 7,29 %, cinq périodes positives/deux
négatives/une neutre, dont deux partielles. Les mois rouges sont acceptés :
rejet économique et robustesse insuffisante. À 1,5x les arrêts de paire changent
les sorties et le total central devient −31,52 $. Pas de suppression du stop
après coup. IC descriptif mensuel 1x central [−0,87 % ; +2,48 %], contient zéro.
Voir [rapport ratio métaux](reports/metals_ratio_2026-09-07/REPORT.md).

Le marqueur brut `RESEARCH_CANDIDATE_UNQUALIFIED` désigne le filtre positif
préliminaire, pas un GO. L'examen complémentaire suspend la règle : environ
7,86 $/30 jours linéaires avant infra, trop faible pour un bot dédié ; net avec
infra hypothétique −88,02 $/206 jours. 239 tests, lint/format 210 fichiers, mypy
61 sources ; 33 artefacts reproduits. Aucun achat, ordre ou changement serveur.

Recherche active. Prochaine qualification envisageable : WTI/Brent, deux frais
réduits ; vérifier spécifications de contrats/oracles et historique natif avant
enregistrement d'un test distinct. Pas d'assimilation automatique à un arbitrage
ni de prétendue réplication du ratio or/argent.

## Brent/WTI hors roulement : règle rejetée — 7 septembre

Spécifications/oracles et dates de roll consultés et archivés ; expositions à
des futures distincts, pas arbitrage garanti. Blackout large jours 4–17 NY,
signal 24 h hors zone, entrées semaine 09–14 h, détention deux heures. Client
public réutilisé pour Brent : neuf requêtes, 0,92 Mo, 3 816 h complètes ; CL
local. Évaluation 1er avril–6 septembre : 158 jours, 18 trades centraux.

PnL 1x total : +8,20 $ brut, −2,54 $ central, −16,38 $ coûts renforcés,
−12,04 $ retard, −2,75 $ funding adverse, hors infra. DD horaire 1,11 % et
enveloppe 3,51 %. Trois périodes positives/deux négatives/une neutre ; rejet
sur total net et économie, pas sur mois rouges. Voir
[rapport pétrole](reports/oil_ratio_2026-09-07/REPORT.md).

Moteur ratio paramétré pour réutilisation : mapping actifs, lookback, horizon,
calendrier ; anciens paramètres par défaut préservés. 241 tests, lint/format
216 fichiers, mypy 62 sources. Trente et un artefacts or/argent inchangés et
32 artefacts pétrole reproduits exactement. Aucun achat, ordre, ancien dépôt
ou serveur modifié. Recherche active ; prochaine qualification : financement
extrême dans les archives natives existantes et réaction des prix, puis
protocole distinct avant tout calcul de stratégie.

## Normalisation du funding — test principal rejeté, anomalie 72 h à répliquer

Règle enregistrée : moyenne funding 8 h >=0,5 bp/h absolu, puis moyenne 4 h
réduite de moitié ; première occurrence, espacement 73 h. Correction et
continuation testées à 24 h, sensibilités 6/72 h. Paiements avec timestamps
natifs, entrée/exit hypothétiques open+60 s ; paiement avant entrée exclu.
19 altcoins ×30 jours et quatre majors ×180 jours, 18 nouveaux appels publics
prix /1,76 Mo, tous les financements réutilisés. Aucun trou/volume nul.

40 événements altcoin : correction −48,71 bps nets moyens ; continuation
+22,61 bps, mais PF1,12 et total négatif sans le meilleur. Quatre événements
majors, tous HYPE : correction +348,85 bps moyens, également négative sans
le meilleur. Les quatre tests principaux sont HYPOTHESIS_NOT_CONFIRMED.
Seulement 19 jours d'entrée altcoin, intervalle prévu non calculable selon
minimum enregistré ; aucun assouplissement après résultat.

Sensibilité 72 h continuation : +642,64 bps nets moyens, +626,83 stress ;
62,19 % du total vient de CASHCAT. Excès vs marché simultané +275,74 bps,
mais −71,27 sans CASHCAT ; excès vs entrées périodiques même actif +111,65,
mais −53,54 sans CASHCAT. Ce sont des événements, pas un portefeuille ni
une validation du drawdown 20 %. Pire événement −23,07 % du notional.
Voir [rapport funding](reports/funding_normalization_2026-09-07/REPORT.md).

245 tests, lint/format 222 fichiers, mypy 63 sources passent. Sept artefacts
reproduits exactement. Recherche active, aucun achat/ordre/changement serveur.
Prochain lot : protocole de réplication antérieure de l'anomalie 72 h, même
univers/seuils, couverture CASHCAT ancienne à vérifier ; cette découverte
descriptive ne remplace pas le test principal rejeté. Comparer aux expositions
simples et simuler le portefeuille uniquement si la réplication le justifie.

### Réplication funding 72 h effectuée — résultat positif mais concentré

Protocole distinct enregistré avant acquisition : 16 juillet–7 août, 22 jours,
mêmes 19 actifs/seuils. CASHCAT local ; 54 appels publics /2,13 Mo pour les
autres, 528 h complètes par actif, aucun volume nul. Dix événements, six dates,
six CASHCAT/quatre XMR. Moyenne nette 72 h +1 218,12 bps, stress +1 201,73,
retard +726,66, funding adverse +1 216,03 ; résultat positif sans meilleur
événement dans les quatre scénarios. Premier bloc légèrement rouge accepté.

CASHCAT représente 95,96 % du total ; pire événement −31,51 % du notional.
Contrôles : marché simultané −35,20 bps moyens, même actif/entrées périodiques
+442,36. Résultat supérieur dans cette fenêtre, mais courte et déjà consultée
pour le hedge CASHCAT. Aucun rendement mensuel ou drawdown de compte validé.
Examen : REPLICATION_EVENT_SCREEN_PASSED_PORTFOLIO_UNQUALIFIED ; test principal
24 h toujours rejeté. Quatre artefacts reproduits, onze avec étude/audit initial.
Lint/format 225 fichiers, source inchangée après 245 tests et mypy 63 sources.

Prochaine action : enregistrer le portefeuille continu 52 jours et ses
comparateurs simples avant tout résultat de sizing. Capital 1 000 $, positions
simultanées/arrondis/funding, coûts 0/20 $ d'infra hypothétique, stress et limite
20 % avec latent/dépassements. Ne pas additionner les événements comme un gain
du compte. Recherche active ; aucun achat, live, service ou serveur modifié.

## Portefeuille funding 72 h — candidat 0,4x, robustesse encore non qualifiée

52 jours continus, 19 actifs, sources locales, aucun reset au 7 août. Capital
1 000 $, allocation partagée, arrondis et minimum 10 $, funding et latent,
arrêt à 20 % sans reprise, enveloppe OHLC avant/après transactions. Marge cross
hypothétique, levier de configuration 2, maintenance stress 20 % du notional ;
snapshot sans restriction isolated et maxLeverage >=3.

Tailles préenregistrées : 0,5x +411,96 $ mais enveloppe 20,94 % ; 1x +417,82 $,
DD horaire 20,05 % et enveloppe 32,18 %, arrêt après 12 trades ; 1,5x −26,60 $,
arrêt après quatre trades. Adaptation enregistrée ensuite : une seule taille
0,4x (−20 % d'exposition), signal inchangé. Calibration sur échantillon vu.

0,4x : 33 trades sur 24 dates, +320,41 $ sans infra (+17,39 % mensuel équivalent),
+280,27 $ avec 20 $/30 jours (+15,32 %), DD horaire 11,24 % et enveloppe 17,85 %
avec infra. Stress coûts +272,24 $ ; retard 1 h +186,15 $ ; funding adverse
+279,63 $ avec infra, tous positifs sous 20 % dans l'enveloppe. CASHCAT apporte
67,91 % des gains de trading ; meilleur cycle +140,86 $, pire −51,70 $,
21,04 jours sous le sommet. Un seul mois complet, août.

Comparateurs 0,4x sans infra : panier conservé +201,95 $, grille long +127,65 $,
CASHCAT seul (plafond par actif) +192,44 $. Risques différents, pas d'alpha
prouvé à risque égal. IC descriptif mensuel central avec infra [+1,90 % ;
+38,72 %], retard [−0,96 % ; +27,60 %], blocs 14 jours /10 000 tirages,
non corrigé pour la sélection et les recherches précédentes. Voir
[rapport portefeuille](reports/funding_portfolio_2026-09-07/REPORT.md).

251 tests, lint/format 231 fichiers, mypy 64 sources. 165 artefacts reproduits,
121 artefacts initiaux inchangés. Aucun ordre, coût ou serveur modifié.
Statut PROMISING_SHORT_SAMPLE_RESEARCH_CANDIDATE, pas GO ni objectif atteint.

Qualification gratuite antérieure : un candleSnapshot CASHCAT 10 mars–16 juillet
ne renvoie que 116 heures, première le 11 juillet à 04:00 UTC. Pas une preuve
de listing, mais pas de
longue réplication disponible par cette requête. Prochaine action : protocole
de transférabilité antérieure sur les autres actifs, même signal et taille 0,4x,
acquisition gratuite bornée des seules données manquantes. Distinguer ce test
d'une réplication CASHCAT. Si dépendance exclusive à son épisode récent,
suspendre la promotion et continuer une autre hypothèse. Recherche active.

## Transfert funding 72 h sur 180 jours — promotion suspendue

144 requêtes natives gratuites, 12,42 Mo, 18 actifs hors CASHCAT tous complets
sur les 128 jours manquants, puis panel 180 jours sans trou ni volume nul.
Même signal et taille 0,4x ; aucun actif écarté après examen de ses résultats.

Simulation continue centrale : −179,44 $ sans infra, −250,29 $ avec 20 $/30 jours,
53 trades, DD observé 20,15 % /enveloppe 22,68 % sans infra, arrêt le 5 juin
06:00 UTC. Les autres scénarios sont négatifs, même zéro coût (−180,06 $).
Le segment récent réinitialisé gagne +95,02 $ sans CASHCAT, mais ne peut pas
être ajouté à un compte arrêté. Rejet sur total net et risque, pas sur mois rouges.
Panier conservé +264,81 $ sur 180 jours ; contrôle non promu.

[Rapport de transfert](reports/funding_transfer_2026-09-07/REPORT.md).
93 artefacts reproduits ; source du moteur inchangée depuis 251 tests/mypy64,
lint/format235 fichiers passent. Aucun achat, live, service ou serveur modifié.
La promotion du candidat récent est suspendue : son épisode positif n'établit
pas un edge robuste généralisable. Les anciennes preuves restent conservées.

Recherche active. Hypothèse suivante : chocs résiduels de rendement d'altcoins
avec couverture BTC, pour limiter la dépendance à une hausse générale.
Réutiliser le panel natif 180 jours ; enregistrer le test avant calcul.

## Chocs résiduels couverts par BTC — échec après coûts

Nouvelle règle enregistrée : OLS sur 28 blocs de six heures antérieurs,
dernier bloc signal exclu, z entre 3 et 6, bêta/corrélation/sigma filtrés,
correction six heures avec hedge BTC à bêta figé. 18 altcoins plus BTC,
180 jours natifs déjà locaux, aucun nouvel appel de données.

504 événements sur 148 dates : +9,25 bps bruts moyens, −3,62 nets centraux,
−18,62 coûts renforcés, −6,06 retard, −4,64 funding adverse. PF 0,91,
IC descriptif 95 % [−16,59 ; +7,24] bps ; total négatif sans meilleur événement.
Deux blocs positifs et quatre négatifs ; rejet sur total net, pas mois rouges.
Horizon 24 h négatif même sans coûts. Aucun sous-univers gagnant sélectionné.

[Rapport chocs résiduels](reports/residual_shocks_2026-09-07/REPORT.md).
254 tests, lint/format 240 fichiers, mypy 65 sources passent ; trois artefacts
reproduits exactement. Réutilisation modèle de hedge, paiements et bootstrap.
Aucun achat, ordre, service ou serveur modifié. Recherche active.

Prochaine hypothèse : rotation hebdomadaire long/short entre altcoins forts et
faibles, à enregistrer avant calcul, avec portefeuille et frais sur le panel
natif disponible. Cette piste doit tester une tendance relative persistante,
pas retoucher les paramètres de la correction six heures rejetée.

## Rotation hebdomadaire — gain trop faible pour poursuivre cette piste

18 altcoins, 180 jours locaux, classement sept jours hors dernière journée,
trois longs et trois shorts chaque lundi, 23 paniers /138 cycles à 0,5x.
Central +81,62 $ sans infra (1,32 % mensuel équivalent), −38,37 $ avec
20 $/30 jours hypothétiques. Stress coûts +62,03 $, retard +81,98 $, funding
adverse +42,80 $ sans infra. Drawdown observé 9,02 %, enveloppe 15,02 %.
Le filtre préliminaire passe à 0,5x sans infra, mais le résultat économique
reste trop faible ; statut de revue POSITIVE_SMALL_RETURN_RESEARCH_SUSPENDED.
Les tailles 1x/1,5x dépassent l'enveloppe de 20 %. Le mois rouge n'est pas un
veto ; 92,67 jours sous le sommet, pire cycle −90,29 $. Aucun GO.

[Rapport hebdomadaire](reports/weekly_relative_2026-09-07/REPORT.md).
63 artefacts reproduits, 257 tests, lint/format245 et mypy66 passent.
Aucun achat, appel de données supplémentaire, ordre ou serveur modifié.
Recherche active : qualifier les contrats, sessions et données gratuites des
actions coréennes pour une hypothèse différente autour de leur ouverture.

## SKHX/NVDA avant préouverture — échec de l'écran économique

Qualification et test terminés. Dix appels natifs gratuits, 1 000 052 octets,
4 320 bougies/fundings SKHX sur 180 jours ; NVDA déjà local. 24 heures SKHX
sans volume, aucune utilisée dans les quatre signaux retenus. Oracle action
coréenne convertie en USD ; préouverture externe avant séance principale.
Deux fermetures omises par XYZ, 3 juin et 17 juillet, ajoutées depuis sources
KRX/Samsung avant calcul. Historique de transitions à la minute non qualifié.

Règle enregistrée : divergence SKHX/NVDA 11–22 UTC, OLS sur vingt dates
antérieures, correction trois heures à partir de 22:01 avec hedge à bêta figé.
Quatre signaux ; proxy 1 000 $ de notional brut constant +8,63 $ central,
−0,42 $ coûts renforcés, −2,64 $ retard 1 h, +6,19 $ funding adverse,
+10,00 $ zéro coût. Central sans meilleur événement −37,99 $. Cela ne
constitue pas un rendement de portefeuille ni une validation du plafond 20 %.
Échec économique et de robustesse, pas veto sur le mois rouge.

[Rapport Corée](reports/korea_opening_2026-09-07/REPORT.md),
[qualification](reports/korea_opening_2026-09-07/QUALIFICATION.md).
Quatre artefacts d'étude et un de qualification reproduits ; 257 tests,
lint/format251 fichiers, mypy66 sources passent. Aucun achat, ordre, secret,
service ou serveur modifié. Statut HYPOTHESIS_NOT_CONFIRMED, aucun GO.

Recherche active : choisir un autre mécanisme à partir des panels gratuits
désormais disponibles ; ne pas ajuster ces quatre événements pour en fabriquer
un candidat. La limite utilisateur reste 20 % de recul depuis le sommet,
positions ouvertes/coûts inclus ; les mois rouges sont acceptés si le total
net est largement positif. Les anciens candidats suspendus le restent.

## Compression puis cassure — rejet, contrôle positif non qualifié

Test enregistré avant calcul sur les 18 altcoins /180 jours natifs locaux.
Plage 24 h <=moitié de sept plages antérieures, cassure avec volume doublé,
24 h de détention, espacement 25 h ; moteur portefeuille existant réutilisé.
234 signaux, 192 cycles centraux à 0,5x : −73,39 $ sans infra, −41,69 $ même
sans coûts. Les trois caps et tous les scénarios sont négatifs. Pas de GO.
Drawdown central 17,02 % observé /17,55 % enveloppe ; retard dépasse 20 %.

Contrôle préenregistré sans compression : 1 593 signaux, 692 cycles centraux
à 0,5x, +290,02 $ sans infra (+4,34 % mensuel équivalent), enveloppe 15,36 %.
Coûts +160,02 $ (+2,50 % mensuel), retard +171,80 $ (+2,68 %), funding adverse
+259,97 $, tous positifs sans infra et enveloppe <20 %. Avec 20 $/30 jours,
central +150,22 $ (+2,36 % mensuel), retard enveloppe 20,19 %. À 1x, arrêt
20,09 % observé /22,37 % enveloppe ; donc pas de multiplication linéaire
des gains pour atteindre 10 %. Contrôle conservé, aucune promotion opportuniste.

Pendant ce calcul, l'utilisateur envisage une cible abaissée à +10 % nets
mensuels et demande si les anciennes pistes deviennent intéressantes.
Réponse : aucun candidat suffisamment validé à ce niveau ; quelques résultats
positifs à quelques pourcents méritent d'être distingués des échecs. Ajouter
la sensibilité +10 % aux évaluations ; plafond de drawdown 20 % inchangé.
Le candidat funding récent reste suspendu après transfert négatif.

[Rapport compression et contrôle](reports/compression_breakout_2026-09-07/REPORT.md).
64 artefacts reproduits exactement, 261 tests, lint/format256 fichiers,
mypy67 sources passent. Aucun nouvel appel de marché, achat, ordre ou serveur.
Statut COMPRESSION_REJECTED_POSITIVE_CONTROL_UNQUALIFIED. Recherche active.

Prochaine action utile : qualifier une fenêtre gratuite supplémentaire pour
le contrôle de cassure, sans changer sa règle ou choisir les actifs gagnants,
avant toute conclusion sur sa robustesse. Distinguer cette nouvelle recherche
de la promotion interdite du simple meilleur contrôle sur la période consultée.

## Tolérance30 % : comparaison calculée, espérance supérieure non démontrée

L'utilisateur accepte un drawdown30 % si l'espérance de gains augmente.
Recherche autorisée à30 %, comparaison20 % conservée ; limites live inchangées.
Moteur portefeuille : paramètre explicite20/30 %, défaut20 %, marge inchangée,
dépassements conservés et aucun rattrapage de pertes. Trente anciennes
simulations20 % économiquement identiques après changement.

Cassure avec volume, mêmes180 jours : à1x, central passe de+69,62 $ sous20 %
à+559,23 $ sous30 % (+7,68 % mensuel équivalent), DD27,30 % /enveloppe29,01 %.
Mais coûts renforcés−138,87 $, retard−151,13 $, drawdowns >30 % ; funding
adverse+473,95 $ mais enveloppe30,45 %. Avec infra20 $/30 j, central+377,38 $
et enveloppe31,38 %. À1,5x, arrêt30 % également. Cap0,5x seul reste filtré
positif sous stress ; aucun résultat net robuste à10 % mensuels démontré.

[Rapport risque30 %](reports/breakout_risk30_2026-09-07/REPORT.md).
63 artefacts reproduits, 263 tests, lint/format261 et mypy67 passent. Aucun
ordre, achat, service ou serveur modifié. Statut HIGHER_RISK_BASE_GAIN_NOT_ROBUST.

Extension native gratuite14 février–10 mars (24 jours) enregistrée : au plus
54 appels séquentiels /5 Mo, même univers18. Acquisition en cours ; analyser
la fenêtre antérieure et la courbe continue204 jours à0,5x, plafonds20/30 %.
Ne pas changer les signaux selon le résultat et ne pas additionner des comptes
réinitialisés. Recherche active.

## Extension de cassure sur 204 jours — positive, encore sous les cibles

Acquisition terminée : 54 appels gratuits, 2 327 340 octets, 18 actifs chacun
576 bougies/fundings supplémentaires, zéro trou/volume nul. Période antérieure
24 jours centrale −46,32 $, coûts −55,46 $, retard −29,56 $, zéro coût −38,55 $.
Ces pertes ne sont pas un veto isolé : compte continu 204 jours central
+255,36 $ sans infra (+3,40 % mensuel), coûts +115,77 $ (+1,62 %), retard
+157,53 $ (+2,17 %), funding adverse +220,94 $. Cap 0,5x seulement.
Enveloppes 15,34–17,38 %, identiques sous seuils 20/30 % sans infra.

Avec infra hypothétique 20 $/30 jours : central +96,21 $, coûts −37,12 $.
Retard : arrêt 20 % et −185,49 $, contre +2,75 $ sans arrêt au seuil 30 %.
783 cycles centraux, 89,33 jours sous sommet, pire cycle −34,61 $. IC descriptif
mensuel central [−2,22 % ; +9,40 %], coûts [−3,92 % ; +7,48 %], blocs 14 jours,
non corrigé pour la sélection. Toujours pas de gain attendu à 10 % démontré.

[Rapport extension](reports/breakout_extension_2026-09-07/REPORT.md).
49 artefacts reproduits, 263 tests du moteur passent, lint/format263 fichiers,
mypy67 sources. Aucun achat, ordre, secret, service ou serveur modifié.
Statut POSITIVE_SMALL_RETURN_EXTENSION_UNQUALIFIED. Acquisition et simulations
terminées ; aucun processus de cette étude encore attendu. Recherche active.

Prochaine piste de recherche : mesurer la covariation des mécanismes positifs
déjà identifiés, puis seulement si elle le justifie tester un portefeuille
à capital partagé et risque global 30 %. Ne pas additionner des rendements
de comptes dotés chacun de 1 000 $, ni choisir des poids après résultat.
Le comparateur long passif doit rester identifiable comme exposition de marché,
pas être présenté comme un alpha validé. Aucun relèvement du risque live.

## Diversification 50/50 — candidat partagé à 6,54 %, non qualifié

Qualification enregistrée : corrélation quotidienne cassures/rotation proche
de zéro sur les quatre scénarios payants du panel 180 jours ; 39 à 43 jours
de pertes communes. Contrôle passif conservé uniquement comme exposition.
Poids 50/50 fixés avant simulation, aucun optimum choisi après résultat.

Moteur étendu : un cash de 1 000 $, budgets séparés selon fractions immuables,
horizons distincts, arrêt global 30 %, pas de prêt du budget inactif. Registre
virtuel par mécanisme, coût/gross/marge/OHLC avant compensation conservateurs.
Caps de recherche 0,5 /1 /1,5 /2x, marge configurée 2 inchangée. Anciennes
branches économiquement identiques sur dix scénarios complets vérifiés.

Sur 204 jours, central sans infra : 0,5x +163,53 $ (2,25 % mensuel),
1x +346,46 $ (4,47 %), 1,5x +538,72 $ (6,54 %), 2x +698,48 $ (8,10 %).
À 1,5x : coûts +236,54 $ (3,17 %), retard +378,88 $ (4,84 %), funding
adverse +381,00 $, enveloppes 27,17–29,41 %, tous positifs sous 30 %.
À 2x, enveloppe centrale 34,63 %, non qualifié. Avec infra hypothétique20 $,
1,5x coûts/retard dépassent légèrement 30 % ; 1x reste seul filtré positif.

1,5x central : 1 065 cycles, contributions cassures +407,99 $ /rotation
+130,73 $, juin −155,33 $, pire cycle −163,03 $, 75,29 jours sous le sommet.
ENA environ −496,65 $ sur les deux mécanismes, aucun retrait après calcul.
IC descriptif mensuel [−2,27 % ; +16,11 %], non corrigé pour la sélection.
Pas d'espérance future ni de cible nette10 % démontrée.

[Rapport diversification](reports/diversification_2026-09-07/REPORT.md).
45 artefacts reproduits, 267 tests, lint/format268 et mypy67 passent. Aucun
achat, appel de marché, ordre, service ou serveur. Tous les calculs de cette
étude sont terminés, aucune attente de processus. Statut
DIVERSIFIED_RESEARCH_CANDIDATE_UNQUALIFIED. Recherche active.

Prochaine qualification : positions nettes natives et risque après compensation,
sans changement de signaux ni poids. Conserver le modèle brut comme référence
conservatrice ; ne pas créditer d'économies de fees/fills sans simulation de
l'exécution réelle. Chercher ensuite une validation gratuite indépendante.

## Qualification nette — petits ajustements à traiter

Audit figé des vingt cas partagés 1,5/2x, 204 jours, sans nouvel appel ni coût.
Cash/equity originaux reconstruits heure par heure, aucune économie créditée.
À 1,5x central : 2 049 deltas nets contre 2 130 jambes virtuelles, dont
18 ajustements <10 $ (11 ouvertures/augmentations et 7 réductions). Aucun
mauvais lot. Les vingt cas ont entre 11 et 25 petits ordres : traduction
directe non qualifiée, sans présumer une exception reduce-only.

Enveloppe nette centrale 1,5x 27,12 %, stress coûts 29,36 % ; 2x central
34,57 % reste hors plafond. Gains originaux inchangés, aucun nouveau GO.
[Rapport netting](reports/netting_2026-09-07/REPORT.md). Huit tests ajoutés,
275 tests complets et mypy68 passent ; reproduction/lint/format consignés.
Aucun ordre, achat, appel de marché, service ou serveur modifié.

Prochain travail : simuler causalement les positions natives effectivement
exécutées, reporter les écarts <10 $ au lieu de les remplir gratuitement,
recalculer funding, frais et risque ; conserver signaux/poids/cap1,5x.
Statut FIXED_NATIVE_DELTAS_REQUIRE_EXECUTION_PLANNER, recherche active.

## Compte natif causal — candidat conservé, dépendance à un épisode favorable

Le planner simulé conserve les écarts non exécutés, réessaie les deltas aux
heures suivantes et dimensionne sur l'equity native. Frais, funding et PnL
portent seulement sur les positions détenues. Arrondi adverse des ticks,
minimum10 $ sans exception présumée, budget natif et arrêt irréversible.
Formule de budgets séparés réutilisée ; dix références complètes identiques.

204 jours /18 actifs, exposition cible1,5x, seuils20/30, cinq scénarios,
infra0/20 hypothétique : vingt cas. À30 sans infra : central+538,26 $
(6,54 % mensuel), coûts+206,49 $ (2,80 %), retard+368,65 $ (4,72 %),
funding adverse+365,41 $ (4,69 %). Enveloppes27,56–29,43 %, tous positifs,
sans incident de marge ni position terminale. Le groupe avec infra20 ne
passe pas30 % en coûts/retard. Le groupe20 % ne passe pas non plus.

Central : 2 022 ordres, 840 tentatives <10 $ et28 refus de budget, 820 heures
d'écart à la cible. Max écart327,67 $ : entrée ARB refusée, pas poussière.
838 épisodes natifs ; un épisode PUMP sur six semaines représente254,36 $
central /206,18 $ stress. Sous stress, sa soustraction comptable laisse
seulement+0,31 $ (pas un replay). IC descriptif mensuel central[−2,27 ;16,12] %,
coûts[−5,58 ;11,79] %. Aucune robustesse ni cible10 % démontrée.

[Rapport compte natif](reports/native_execution_2026-09-07/REPORT.md).
Registre indépendant cash/inventaire réconcilie chaque equity horaire,
coût/funding/drawdown, tous les lots/minimums/ticks et budgets d'entrée
des vingt cas. 289 tests, mypy69, lint/format vérifiés ; artefacts reproduits.
Aucun achat, appel de marché, ordre réel, service ou serveur modifié.
Statut NATIVE_EXECUTION_RESEARCH_CANDIDATE_UNQUALIFIED, recherche active.

Prochaine recherche : épreuve de généralisation sur une autre période/régime
et contrôle passif. Qualifier les archives publiques gratuites disponibles
avant acquisition ; une série d'une autre plateforme est un test de transfert,
pas une preuve de fills Hyperliquid. Conserver signaux et poids, ne pas
retirer de gagnant/perdant après résultat. Le prix open+60 s et la liquidité
d'exécution restent à qualifier.

## Transfert2025 et contrôle passif — généralisation non confirmée

Qualification et acquisition gratuites terminées :15 contrats Binance
existants avant2025,360 archives mensuelles ZIP vérifiées par CHECKSUM et
SHA-256.721 appels publics /7 468 429 octets incluant la qualification.
8 760 heures par actif, aucun trou/volume nul, fundings complets4h/8h.
LIT/PUMP/XPL exclus du seul transfert par dates de contrat avant PnL.

90 simulations : panel natif18, sous-panel natif15 sur204 jours2026 et
transfert Binance15 sur2025 ; candidat inchangé et passifs0,5/1,5x.
Le candidat2025 perd270,83 $ central,262,08 $ en coûts,298,88 $ en retard,
264,46 $ sans coûts ; arrêt le19 janvier, dépassements conservés. Deux
épisodes FARTCOIN perdent136,97 $ et116,93 $, frais totaux5,14 $ seulement.
Ne pas retirer cet actif après résultat. Aucun scénario2025 ne passe.

Passif0,5x : natif18 +292,53 $ /3,85 % mensuel, enveloppe16,98 %, mais
transfert2025−244,20 $ et arrêt6 avril. Passif1,5x échoue aussi. Sur le
sous-panel natif15, le candidat reste positif mais dépasse30 % d'enveloppe
en coûts32,18 % et retard34,49 %. Distinguer effets d'univers et de période.

[Rapport transfert](reports/prior_transfer_2026-09-07/REPORT.md). Statut
SHARED_STRATEGY_GENERALIZATION_NOT_CONFIRMED : promotion du candidat récent
suspendue. Anciens artefacts positifs conservés, aucun GO/objectif10 % validé.
Le transfert n'est pas une reconstitution native Hyperliquid2025 ; prix,
volume/funding Binance et contraintes économiques Hyperliquid sont nommés.

98 artefacts reproduits à l'identique, vingt anciennes références natives
complètes inchangées.298 tests, lint/format288, mypy70 passent. Aucun achat,
ordre réel, service ou serveur modifié. Tous les processus de cette étude
sont terminés ; recherche active, aucune acquisition ou simulation attendue.

Prochaine hypothèse : tendance plus lente et pondération par volatilité
passée, cap brut fixe, sans suppression des perdants ni rattrapage par levier.
Utiliser les données2025/2026 disponibles, enregistrer les règles avant PnL,
et ne pas appeler une variante choisie après ces recherches une validation
indépendante. Suspendre toute piste qui exige une dépense.

## Tendance lente et volatilité — filtre entre périodes échoué

Règles fixées avant calcul : signe du rendement propre sur 30 jours, paniers
du lundi conservés 168 heures, poids inverses de volatilité quotidienne passée
avec plancher 1 %, contrôle à poids égaux. Caps fixes 0,5/1,5x, seuil global
30 %, aucune suppression d'actif ni augmentation de levier après perte.
Warmup : premières entrées 3 février 2025 /23 mars 2026 ; le choc du 19 janvier
n'est donc pas rejoué. Panneaux natifs 18/15 et transfert Binance 15 conservés.

À 0,5x sans infra, pondéré : natif18 −36,42 $, natif15 +12,09 $ mais funding
adverse −14,81 $, transfert2025 +126,41 $. Équivalents mensuels −0,54 %,
+0,18 %, +0,98 %. À 1,5x, enveloppes centrales 36,22 /34,16 /32,65 % :
hors plafond. Poids égaux non concluants non plus. Cinq cas natifs avec
infra hypothétique 20 $ conservent un résidu terminal, explicitement marqué.

[Rapport tendance lente](reports/slow_trend_2026-09-07/REPORT.md). Statut
SLOW_TREND_CROSS_PERIOD_SCREEN_FAILED : aucune promotion ni cible10 % prouvée.
120 simulations /132 artefacts reproduits ; 30 anciennes références complètes
identiques.304 tests, lint/format293, mypy71 passent. Aucun achat, appel de
marché, ordre réel, service ou serveur. Tous les calculs sont terminés.

Prochaine famille : effets temporels autour des règlements de funding,
signaux ex ante, fenêtres prédéfinies et contrôle des heures sans paiement.
Utiliser d'abord les données existantes ; ne pas répéter le simple classement
de portage relatif déjà rejeté sur les quatre majors. Recherche active.

## Horaires de funding — filtre événementiel négatif

Règle ex ante enregistrée : après un taux précédent de valeur absolue
>=10 bps, prévoir le prochain règlement à partir de l'intervalle observé,
entrer dans le sens du taux à +60 s, garder une heure. Contrôle apparié
à +2 h, stress de retard +1 h. Aucun taux futur dans le signal.

Archives Binance 2025 déjà présentes : 113 événements /62 jours, 39 longs
et 74 shorts, 113 horaires concordants. ZEC50/XMR45 dominent l'échantillon.
Moyenne principale −21,81 bps central, −36,84 coûts, −11,24 retard,
−8,79 sans coûts. Contrôle +7,09 central mais −7,91 en coûts. PF0,672,
pire événement −498,46 bps. Aucun paiement pendant les fenêtres ; aucune
collecte fictive du funding réglé avant l'entrée. Intervalle descriptif de
l'avantage apparié [−71,18 ;17,53] bps : hypothèse non confirmée.

[Rapport horaires de funding](reports/funding_clock_2026-09-07/REPORT.md).
Statut FUNDING_CLOCK_HYPOTHESIS_NOT_CONFIRMED ; pas de portefeuille ni
d'acquisition supplémentaire justifiés, aucun GO/rendement mensuel déduit.
Trois artefacts reproduits, 310 tests, lint/format298, mypy72 passent.
Aucun nouvel appel de marché, achat, ordre réel, service ou serveur modifié.
Tous les calculs sont terminés ; recherche active.

Prochaine piste : modèle conditionnel simple entraîné sur le passé, évalué
chronologiquement, avec labels purgés selon leur date de disponibilité.
Fixer variables/régularisation/horizon/seuil avant calcul, pas de réglage
sur les fenêtres d'évaluation. Réutiliser données et moteur natif ; ne pas
présenter des périodes déjà explorées comme une validation prospective.

## Modèle conditionnel — filtre entre périodes échoué

Ridge à huit variables passées (tendance, volume, funding), horizon6h,
seuil40bps et régularisation1 fixés avant PnL. Réentraînement mensuel sur
90 jours, labels connus depuis au moins1h ; modèle gelé et normalisation
apprise sur les seules données admissibles. Trois panneaux déjà disponibles.

Évaluation native à partir du1 juin2026 :18 actifs144 événements/28 jours,
moyenne centrale−52,86bps, coûts−67,84, zéro coût−40,14. Sous-panel15 :
123/28, central−22,44, coûts−37,45, zéro−9,91. Transfert2025 à partir
du1 avril :373/121, central+30,46, coûts+15,41, retard+28,60, mais borne
inférieure95 %−27,97bps et contribution ZEC supérieure au gain total.
Erreur quadratique légèrement pire que la moyenne seule sur chaque panneau.

[Rapport modèle conditionnel](reports/conditional_model_2026-09-07/REPORT.md).
Statut CONDITIONAL_MODEL_CROSS_PERIOD_SCREEN_FAILED : aucun panneau ne passe,
aucun portefeuille ni GO justifié. Ne pas ajuster le seuil ni retirer les
perdants après résultat. Ce résultat ne condamne pas tout modèle statistique.

315 tests, lint/format303 fichiers, mypy73 sources ;15 artefacts reproduits
à l'identique. Dates de purge, coefficients/prévisions et tous les événements
au seuil audités. Aucun nouvel appel de marché, achat, ordre réel, service
ou serveur. Tous les calculs de cette étude sont terminés ; recherche active.

Prochaine famille : classement par volatilité passée, long des moins volatils
et short des plus volatils, paniers hebdomadaires sans signal de tendance.
Fixer le protocole avant PnL ; utiliser les panneaux2025/2026 existants et
conserver les limites du transfert et de la sélection historique. Le risque
30 % et le compte1 000 $ restent à simuler seulement si le filtre économique
justifie cette étape ; aucune hausse automatique du levier après perte.

## Classement par volatilité — ventes des actifs agités non rémunérées

Protocole fixé : volatilité quotidienne sur30 rendements passés, lundi00h,
trois achats calmes/trois ventes agitées à notionnels égaux, garde168h.
Contrôle acheteur des mêmes six actifs. Données existantes, aucun achat.

23 paniers natifs18/15 à partir du23 mars2026 et47 paniers Binance15 à
partir du3 février2025. Principal central−191,53 /−102,38 /−80,69bps par
panier et par unité de notionnel brut ; même zéro coût négatif partout.
Les longs sont positifs, les shorts les dépassent en pertes. Aucun panneau
ne passe le filtre. Statut VOLATILITY_SPREAD_HYPOTHESIS_NOT_CONFIRMED.

Contrôle acheteur central+278,57 /+189,56 /+134,35bps, quatre scénarios payants
positifs partout mais intervalles95 % incluant zéro et forte concentration.
Meilleure semaine native18 +48,47 % du notionnel ; pire−12,37 %. Ne pas
convertir la moyenne hebdomadaire en espérance mensuelle, ni promouvoir le
contrôle après résultat. Pas de compte partagé, marge ou drawdown validés.

[Rapport volatilité relative](reports/volatility_spread_2026-09-07/REPORT.md).
Douze artefacts reproduits, classements/agrégats/contrôles audités.319 tests,
lint/format308 fichiers, mypy74 sources passent. Aucun nouvel appel de marché,
achat, ordre réel, service ou serveur modifié. Tous les calculs sont terminés.

Prochaine étape : qualifier une période gratuite plus ancienne pour le panier
acheteur des six extrêmes de volatilité, sans changer classement/poids. Ce
choix est explicitement postérieur aux résultats du contrôle ; il constitue
une nouvelle hypothèse, pas une promotion. Les métadonnées2025 déjà stockées
permettent de sélectionner avant PnL les contrats existant avant2024 (11 sur15,
hors ENA/FARTCOIN/JUP/TAO). Qualifier schémas/couverture/coûts de collecte avant
acquisition ; conserver contrôles d'univers et les limites du transfert.
Risque natif1 000 $/30 % à vérifier si les résultats le justifient. Recherche active.

## Épreuve2024 du contrôle acheteur — collecte finie, divergence de données

Paramètre d'année ajouté aux outils d'archives existants, défaut2025 préservé.
Les360 archives2025 revalidées donnent exactement la qualité précédente.
Onze contrats retenus par dates avant2024 ; règles acheteuses inchangées,
contrôle hebdomadaire équipondéré des onze. Protocole économique enregistré
avant PnL de ce sous-panel ; choix de la stratégie explicitement postérieur
au contrôle positif de volatility_spread.

Natif11/2026 :23 paniers, moyenne centrale+175,90bps contre+176,28 au contrôle.
Transfert11/2025 :47 paniers,+88,46 contre+34,12bps. Les quatre scénarios
payants positifs, mais les bornes95 % restent négatives. Huit artefacts
reproduits et agrégats audités. Aucun GO ni compte partagé/drawdown validés.

Acquisition2024 terminée :264 ZIP,528 appels incluant qualification et
CHECKSUM. Diagnostics supplémentaires14 appels, total542 /5 709 699 octets,
0 $ de données.8 784 heures/actif et fundings complets ; pourtant le loader
rejette une bougie de volume nul pour chaque actif le28 octobre20h UTC.
La vue partielle cinq actifs et son rejet sont conservés.

Comparaison de tout octobre avec REST officiel :22 différences, les mêmes
deux heures20h/21h pour les onze actifs ;8 162 autres lignes égales. ARB
journalier reproduit l'anomalie mensuelle, REST donne du volume positif.
Deux requêtes REST ARB concordent sur leur recouvrement. Aucune correction
implicite, aucun PnL2024 encore calculé, aucune sélection d'actif sur gain.

[Rapport épreuve2024](reports/volatility_long_2024_2026-09-07/REPORT.md).
Statut OLDER_YEAR_OFFICIAL_SOURCES_DISAGREE_CORRECTION_REQUIRED.321 tests,
lint/format312 fichiers, mypy74 sources passent. Tous les processus sont
terminés ; aucun achat, ordre réel, service ou serveur modifié. Recherche active.

Prochaine action : enregistrer avant PnL un amendement de priorité de source,
vue dérivée REST explicite sur les deux heures litigieuses de tous les actifs,
archives originales et défaut strict conservés. Tester les corrections
incomplètes/extra-période et revalider2025/2026. Puis lancer2024 sans changer
stratégie ni seuils. Les fichiers d'enregistrement/résultatsv1 et le code
économique exact sont conservés ; créer des artefactsv2 distincts.

## Correction2024 et résultat acheteur — moyennes positives, filtre non passé

Vue dérivée explicite REST :22 bougies corrigées aux deux heures enregistrées,
archives intactes et rejet brut conservé. Vérification des744 heures REST
par actif et égalité OHLCV de toutes les autres heures. Le défaut2025 demeure
identique ; tests de portée, complétude, volume et mauvaise année réussis.
Amendement enregistré avant premier PnL2024. Aucun nouvel appel réseau.

47 paniers2024 : central+218,52bps du notionnel brut, coûts+203,27,
retard+234,16, funding adverse+206,88 ; contrôle+173,08. Avantage moyen
+45,45bps mais intervalle95 %[−22,31 ;126,91]. Pire semaine−20,41 %.
Les panneaux2025/2026 restent entièrement inchangés :+88,46 /+175,90bps
centraux, avec bornes inférieures95 % négatives. Aucune performance du compte
1 000 $ ni drawdown natif30 % n'est encore déduit.

[Résultatsv2](reports/volatility_long_2024_2026-09-07/RESULTS_V2.md).
Statut VOLATILITY_LONG_POSITIVE_HISTORY_STATISTICAL_GATE_FAILED : trois
périodes positives après coûts, mais aucun panneau ne passe le filtre complet.
La concentration ZEC2025 et l'absence d'avantage natif2026 restent visibles.
Aucune promotion. Douze artefactsv2 reproduits, huit contrôles économiques
v1/v2 identiques ;325 tests, lint/format316 fichiers, mypy75 sources passent.
Tous les calculs terminés, aucun achat, ordre réel, service ou serveur modifié.

Prochaine action : enregistrer séparément un diagnostic de faisabilité du
capital1 000 $ avec moteur natif, mêmes signaux et benchmark, caps fixes et
arrêts20/30 %. Ce diagnostic postérieur aux résultats répond à la contrainte
de risque ; il conserve l'échec statistique et ne constitue pas une promotion
de la stratégie. Ne pas modifier les seuils du filtre précédent ni sélectionner
de nouveaux actifs/poids sur le PnL. Recherche active.

## Diagnostic du capital — piste acheteuse incompatible entre périodes

240 simulations enregistrées avant calcul, moteur natif inchangé :3 panneaux11,
candidat/contrôle, caps0,5/1,5x, arrêts20/30 %,5 scénarios, infra0/20 hypothétique.
Signaux et qualité identiques aux artefactsv2 ; aucun effacement de l'échec
statistique antérieur. Pas de reprise après arrêt ni hausse du cap après perte.

Central0,5x/30 % sans infra :2024+6,19 $ /0,05 % mensuel, arrêt5 août,
enveloppe31,77 % ;2025+180,65 $ /1,37 %, enveloppe26,91 % ;2026+201,11 $
/2,73 %, enveloppe13,88 %. À1,5x :+907,10 /−273,62 /+127,97 $, enveloppes
35,46 /36,71 /33,79 %, tous arrêtés. Aucun groupe règle/cap/limite/infra
ne passe les douze cas payants entre périodes. Contrôle non concluant aussi.

La trajectoire2024 est fragile : coût stress0,5x/30 %+555,47 $ car les
ajustements modifiés évitent l'arrêt horaire central, mais enveloppe30,59 %
hors limite. Funding adverse−5,84 $. Ne pas sélectionner le stress gagnant.
Infra20 central0,5x/30 % :−163,77 /−85,12 /+42,53 $. Les premières positions
restent après le warmup ; aucun test du choc19 janvier2025 dans ce diagnostic.

[Rapport capital](reports/volatility_capital_2026-09-07/REPORT.md). Statut
VOLATILITY_CAPITAL_CROSS_PERIOD_RISK_SCREEN_FAILED.252 artefacts reproduits,
240 registres cash/inventaire audités indépendamment, vingt anciens audits
exactement inchangés. Tous les comptes terminent plats, sans incident de marge
dans le modèle.325 tests complets,23 ciblés, lint/format319 et mypy75 passent.
Aucun nouvel appel, achat, ordre réel, service ou serveur. Tous les processus
terminés ; recherche active, aucune cible10 % ni promotion validée.

Prochaine hypothèse : condition de tendance collective prédéfinie pour
l'exposition acheteuse ou le cash ; aucune sélection nominative sur pertes.
Tester2024–2025 en chronologie continue, sans remise à zéro annuelle du
warmup/capital, avec le panneau natif séparé. Enregistrer les règles avant
PnL ; préserver le comparateur non conditionné et les échecs précédents.

## Tendance collective — comparaison 20/30 % terminée

Condition enregistrée avant calcul : médiane des rendements passés sur 30 jours
positive pour autoriser le panier acheteur hebdomadaire. Compte continu
Binance 2024–2025, 731 jours sans remise à zéro annuelle, et natif 2026 séparé,
204 jours. Univers onze inchangé. 99 dates continues dont 42 admissibles,
23 natives dont dix admissibles ; 94 anciens classements continus identiques
et cinq semaines nouvellement couvertes. Aucun changement du moteur natif.

À 0,5x sans infrastructure, élargir l'arrêt de 20 à 30 % change le central
continu de −0,83 à +582,16 $ (1,90 % mensuel composé, enveloppe 27,55 %).
Mais le natif reste +2,29 $ (0,034 % mensuel), coût stress −0,91 $ et funding
adverse −5,20 $. À 1,5x / 30 %, les enveloppes centrales 35,44 / 33,80 %
dépassent la limite et les gains diminuent par rapport à l'arrêt 20 %.
Zéro groupe compatible sur seize ; cible 10 % et promotion non validées.

Le compte continu garde ses positions du 30 décembre jusqu'au 6 janvier ;
aucune nouvelle entrée les quatre lundis de janvier, sans effacement du gain
de transition. Novembre 2024 apporte 423,19 $ sur 582,16 $ au total ; la plus
longue période sous le sommet atteint 305 jours. Cette condition n'est donc
pas retenue pour le déploiement.

[Rapport](reports/collective_trend_2026-09-07/REPORT.md), statut
COLLECTIVE_TREND_CROSS_PERIOD_SCREEN_FAILED. 160 simulations et audits comptables
indépendants, 172 artefacts reproduits à l'identique ; 40 contrôles natifs
intégralement identiques au diagnostic précédent. Tous les comptes terminent
plats, sans incident de marge modélisé. 328 tests, lint/format et mypy passent.
Aucune nouvelle donnée achetée ou collectée, aucun ordre réel, service ou
serveur modifié. Tous les calculs terminés ; recherche active, aucun GO.

## Carry relatif hebdomadaire — hypothèse non confirmée

Nouvelle règle enregistrée avant PnL : acheter les trois sommes hebdomadaires
de funding les plus faibles et vendre les trois plus élevées, uniquement si
la recette estimée dépasse 13 bps de coûts centraux. Garde 168 h, onze actifs
prédéfinis, Binance 2024–2025 continu et Hyperliquid 2026. Le premier registre
reste conservé ; v2 corrige seulement le format et son chemin avant tout calcul.

42 paniers continus et 23 natifs. Funding effectivement reçu +20,20 / +17,44 bps
du notionnel brut par panier, mais prix −18,66 / −29,87 et frais/slippage
−13,06 / −13,08 : net central −11,51 / −25,50 bps. Coûts renforcés −26,58 /
−40,59 ; retard −22,19 / −32,10. Les deux années Binance sont négatives
séparément par date d'entrée. Contrôle inversé également non concluant.
Aucune simulation de capital justifiée, aucune conversion en objectif mensuel.

[Rapport](reports/weekly_carry_2026-09-07/REPORT.md), statut
WEEKLY_CARRY_CROSS_PERIOD_SCREEN_FAILED. Huit artefacts reproduits à l'identique ;
3 900 combinaisons jambe/règle/scénario auditées par comptabilité indépendante,
calendrier et sélection causale vérifiés depuis les sources. 331 tests complets,
lint/format 329 fichiers, mypy 77 sources passent. Aucune acquisition, dépense,
ordre réel ou modification serveur. Tous les calculs terminés ; aucun GO.

Prochaine piste à formaliser avant PnL : réponse d'un panier d'actifs à un choc
baissier commun, continuation contre rebond. Réutiliser les panneaux continus
pour tester un mécanisme de prix intrajournalier distinct du revenu de funding,
sans sélectionner les actifs ou les dates sur leurs pertes. Recherche active.
