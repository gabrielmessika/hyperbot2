# Diagnostic L4 0xArchive — 7 septembre 2026

L’accès manquant est résolu. **Reconstruction historique validée sur les
échantillons ; exécution toujours `DATA_BLOCKED` ; aucun GO économique.**
La clé fournie a servi à des requêtes de données et à trois témoins WebSocket
bornés. Aucun ordre, achat ou service permanent lancé.

## Résultats

| Contrôle | Résultat |
|---|---|
| Authentification REST et WebSocket | Fonctionnelle avec la clé fournie |
| Premier essai BTC YES/NO, 10 s | Deux checkpoints exacts, 44 diffs |
| BTC/ETH/SOL/HYPE YES/NO, 60 s | Huit checkpoints exacts, 369 diffs |
| Fusion YES + complément NO contre Hyperliquid natif | 3/3 captures exactes, cinq niveaux des deux côtés : prix, tailles, nombres d’ordres |
| Fraîcheur d’exécution au serveur | Aucun événement admissible avec les hypothèses actuelles |
| Qualification de file, fills, rentabilité | Non acquise |

Les quatre fenêtres de reconstruction portent sur le 6 septembre, de
16:00:00 à 16:01:00 UTC : outcomes 1715 à 1718. Diffs par carnet : BTC 17/82,
ETH 10/95, SOL 5/4, HYPE 1/155. La comparaison native utilise trois captures
BTC du 6 septembre à 16:49:14.349, 16:49:41.742 et 16:50:09.179 UTC,
réutilisées du diagnostic précédent. Aucune collecte d’un mois nécessaire
pour établir ces résultats techniques.

Le reconstructeur réutilise ses contrôles stricts, `Decimal`, l’ordre de
priorité fourni et les insertions explicites. La nouvelle fusion ajoute la
liquidité complémentaire NO au carnet YES et refuse doublons et croisement.
Elle calcule une profondeur économique ; elle ne prouve pas la priorité
d’exécution entre ordres provenant des deux carnets.

## Mesures temps réel

Trois captures de 30 s sur BTC 1896, alors actif (échéance le 8 septembre à
06:00 UTC), sans reconnexion. Les âges sont `réception locale − timestamp
d’événement fournisseur` ; ce ne sont ni une latence d’ordre ni une mesure de
couverture temporelle. Les captures ont lieu à des instants différents.

| Source et canal | Événements | Âge min. | Médiane | P95 | Âge ≤ 500 ms | Âge ≤ 100 ms |
|---|---:|---:|---:|---:|---:|---:|
| Local, `hip4_l4_diffs` | 218 | 1 443 ms | 2 155 ms | 2 380 ms | 0 | 0 |
| Serveur, `hip4_l4_diffs` | 156 | 484 ms | 541 ms | 2 125 ms | 16 | 0 |
| Serveur, `hip4_l4_orders` | 269 | 486 ms | 585 ms | 2 120 ms | 11 | 0 |

Le budget actuel exige `âge + placement 350 ms + incertitude 50 ms ≤ 500 ms`,
soit un âge maximal de 100 ms. Les 350 ms restent une hypothèse héritée,
sans mesure d’ordre. Même sans cette hypothèse, les queues de distribution
dépassent deux secondes. Le relevé NTP final du serveur indique +1,393 ms ;
il ne prouve pas la synchronisation de toutes les horloges pendant les captures.

Les snapshots initiaux serveur ont des horodatages d’enveloppe apparemment
frais (78/81 ms), contrairement aux diffs suivants. Ce timestamp ne doit pas
devenir une preuve de complétude de chaîne. Le canal orders a fourni des
événements de cycle d’ordre, sans snapshot initial. Aucun champ `seq` observé
dans les diffs WebSocket ; l’ordre local des messages ne suffit pas à démontrer
l’absence d’omissions fournisseur.

## Accès, couverture et coût observé

Le dernier en-tête de compte indique 50 000 crédits, 38 utilisés, 49 962
restants. Il s’agit d’un relevé du compte, sans extrapolation du coût mensuel
du WebSocket. La route de couverture testée renvoie `data_types: {}` : elle
ne constitue donc pas une preuve de couverture sans trous. La route freshness
du marché courant expose un carnet ancien malgré un flux L4 actif ; son champ
orderbook ne valide pas la fraîcheur du canal L4.

Les historiques L4 sont classés B. Les horloges locales ajoutées aujourd’hui
ne permettent pas de reconstituer la réception historique. Une égalité aux
checkpoints n’exclut pas des transitions intermédiaires manquantes ou la
compensation de plusieurs erreurs.

Les routes REST et le modèle de carnet sont décrits par
[0xArchive L4](https://docs.0xarchive.io/rest-api/order-books-l4). Les canaux
et contraintes de transport sont documentés dans
[WebSocket L4](https://docs.0xarchive.io/websocket/l4-orderbook) et
[les canaux](https://docs.0xarchive.io/websocket/channels). Les plafonds de
compte sont à rapprocher des [limites publiées](https://docs.0xarchive.io/rate-limits).
Les conclusions chiffrées ci-dessus viennent de nos captures, pas d’une
promesse de latence du fournisseur.

## Livraison et reproduction

Lecture de la clé brute ou nommée, témoin L4 borné, fusion de profondeur et
audit offline livrés. Réutilisation du stockage HyperBot, des contrats de
provenance, des checksums et du reconstructeur existants. **167 tests passent**,
lint/format et typage des 44 modules source vérifiés. Tests de perte de flux
et d’écho de secret ajoutés. La clé est hors Git, en 0600 localement et sur le
serveur ; son contenu n’est pas inclus dans les artefacts.

Les témoins serveur ont utilisé le bundle `b77d6b7cf57de9a9`. Le manifeste
[d’installation finale](server_research_install.json) identifie le bundle des
outils terminés ; le runtime `b44a0baa421ac7f2` reste inchangé. Aucun ancien
bot relancé. Les raws serveur sont conservés sous
`/opt/hyperbot2/shared/data/archive-l4-2026-09-07-{diffs,orders}` ; les réponses
REST et copies des témoins sont dans `data/l4_2026-09-07/`, hors Git.

[L’audit offline](offline_audit.json) reproduit les huit reconstructions,
les trois comparaisons natives et les distributions des trois témoins, en
vérifiant les checksums. Commande complète dans
[la procédure](../../docs/L4_RESEARCH.md). Les manifestes identifient sources,
périodes et versions de code. Aucun backtest économique ou modèle de fill
n’est exécuté dans cette vague ; frais et latence de fill ne sont donc pas
présentés comme validés.

## Prochaine piste et critères d’arrêt

La clé lève le blocage d’accès, pas ceux de fraîcheur et de qualification.
La prochaine expérience utile est une comparaison **simultanée et bornée**
entre L4 fournisseur et L2 natif, depuis le serveur : même outcome actif,
horloges communes, profondeur duale comparée après blocs complets seulement.
Objectif : distinguer le retard d’événements du retard effectif du carnet et
mesurer des fenêtres utilisables sans transformer une enveloppe récente en
preuve de complétude. Un gap, une divergence ou une continuité indémontrable
doit maintenir le blocage. Une nouvelle capture reste de la qualification
technique, sans optimisation sur ces fenêtres déjà consommées.

Un GO maker exigerait ensuite les preuves de continuité, de priorité duale,
de référence causale, de frais et de fills central/pessimiste, puis les gates
A/OOS/shadow du plan. Si les fenêtres d’exécution restent non qualifiables,
arrêter cette piste maker avec ce transport. Les alternatives taker, funding
et paniers déjà testées restent rejetées selon le
[rapport précédent](../search_2026-09-06/REPORT.md). Aucun résultat ici ne
valide la cible de +30 % par mois.
