# Épreuve2024 : archives acquises, désaccord de sources à traiter

**Mise à jour : correction explicite validée et épreuve2024 terminée.**
Les moyennes sont positives sur les trois panneaux, mais le filtre statistique
échoue. Voir [les résultatsv2](RESULTS_V2.md). Le texte ci-dessous conserve
le diagnostic initial ; l'attente de correction n'est plus le statut courant.

**La collecte gratuite est terminée, mais le rendement2024 n'est pas encore
calculé.** Les archives mensuelles/journalières et l'API officielle actuelle
divergent sur deux heures. Le loader strict rejette le panneau brut ; aucune
bougie n'a été corrigée implicitement pour faire passer un test financier.

## Travail économique déjà effectué

Le contrôle acheteur des six extrêmes de volatilité est une hypothèse choisie
après les résultats de volatility_spread. Son épreuve plus ancienne est fixée
dans le [protocole économique](ECONOMIC_PROTOCOL.md), enregistré avant tout
PnL du nouveau sous-panel. Il ne s'agit pas d'une validation indépendante
de l'ensemble de la recherche.

Onze contrats existent avant2024 selon les métadonnées déjà stockées : ARB,
BNB, DOGE, INJ, LINK, NEAR, UNI, WLD, XMR, XRP et ZEC. Les mêmes onze actifs
sont comparés sur2024/2025/2026. Les exclusions sont exclusivement liées aux
dates de contrat ; aucun actif perdant n'a été retiré.

Sur les données déjà disponibles, le classement et les poids sont inchangés :
trois volatilités faibles/trois fortes, toutes achetées à notionnels égaux,
rééquilibrage hebdomadaire. Le contrôle achète les onze actifs à parts égales.

| Panneau11 | Paniers | Candidat central moyen | Contrôle central moyen | Avantage candidat |
|---|---:|---:|---:|---:|
| Hyperliquid2026 | 23 | +175,90bps | +176,28bps | −0,38bps |
| Binance2025 | 47 | +88,46bps | +34,12bps | +54,34bps |

Ces moyennes portent sur le notionnel brut initial hebdomadaire, pas sur un
compte de1 000 $. Les quatre scénarios payants restent positifs pour les deux
règles, mais les intervalles95 % centraux du candidat incluent des pertes :
[−134,24 ;+580,11]bps et [−179,54 ;+397,32]bps. Aucun GO ; avantage nul sur2026.
Huit artefacts reproduits à l'identique, agrégats à notionnels égaux audités.

## Qualification et collecte2024

[Protocole de qualification](QUALIFICATION_PROTOCOL.md), métadonnées anciennes
réutilisées et échantillon ARB janvier validé.264 ZIP annuels pour11 actifs,
avec CHECKSUM fournisseur et SHA-256 local.8 784 bougies par actif,2024 étant
bissextile ; horaires et OHLC contrôlés, calendriers complets de funding.

La collecte et ses diagnostics représentent **542 appels publics /5 709 699
octets /0 $ d'achat de données** :528 appels ZIP/CHECKSUM incluant l'échantillon,
trois appels de diagnostic et onze lectures REST mensuelles. Les deux fichiers
de l'échantillon ne sont pas téléchargés à nouveau. Aucun appel signé.
Les archives restent append-only et hors Git.

L'outil de qualification, le fetcher et le loader existants ont reçu un
paramètre d'année explicite ;2025 reste le défaut. Le contrôle de régression
recharge les360 archives2025 et retrouve exactement la qualité publiée.
Deux nouveaux tests couvrent l'année bissextile et le rejet d'un manifeste
d'une autre année. [Régression2025](loader_2025_regression.json).

## Désaccord localisé, sans preuve d'une heure sans marché

Pour chacun des onze actifs, le ZIP mensuel contient une bougie de volume nul
le **28 octobre2024 à20h UTC**, avec OHLC constant et zéro transaction. Le
loader rejette correctement ces archives comme panneau directement exploitable.
L'archive journalière ARB reproduit cette anomalie.

L'API publique actuelle restitue une bougie de volume positif à cette heure,
et une autre bougie différente à21h. La comparaison a été étendue aux744
heures d'octobre pour chacun des onze actifs : **22 bougies différentes,
exactement20h et21h le28 octobre ; les8 162 autres concordent numériquement**
sur les douze colonnes. La requête ARB limitée à trois heures concorde avec
la requête mensuelle sur leur recouvrement.

Cette preuve établit un désaccord de sources ; elle ne prouve pas à elle
seule que chaque champ REST est la vérité définitive. Binance indique que
des archives peuvent être révisées pour corriger des problèmes découverts
après publication. [Documentation officielle des archives](https://github.com/binance/binance-public-data).
Le détail original des deux versions est conservé dans
[l'audit de divergence](archive_discrepancy_audit.json).

## Décision et travail restant

Statut **OLDER_YEAR_OFFICIAL_SOURCES_DISAGREE_CORRECTION_REQUIRED**. Ce n'est
pas une impasse payante. Avant de calculer le PnL2024, il faut enregistrer
une priorité de sources explicite, puis construire une vue dérivée utilisant
les bougies REST pour les deux heures litigieuses de tous les actifs.
Conserver les ZIP originaux, leurs checksums et l'échec du loader par défaut.
Tester le rejet d'une correction incomplète ou touchant une autre période,
et la stabilité des données non concernées. Aucun changement de stratégie.

L'enregistrement économique initial et les résultats2025/2026 restent
immuables ; une version suivante devra identifier l'amendement de données
et reproduire les résultats non concernés avant d'évaluer2024. Pas de marge,
lots, exécution native, drawdown30 % ou rendement mensuel validés ici.

321 tests, lint/format312 fichiers, mypy74 sources passent. Tous les processus
de qualification, collecte, diagnostic et calculs de ce lot sont terminés.
Aucun achat, ordre réel, service ou serveur modifié. Recherche active.
