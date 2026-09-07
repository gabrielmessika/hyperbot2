# Diagnostic maker terminé — 7 septembre 2026

**Décision : NO-GO pour le candidat maker HIP-4 avec le transport et les
hypothèses actuels.** Suspendre cette piste ; ne pas lancer de collecte
permanente ou de trading. Le statut d’exécution reste `DATA_BLOCKED`.
Cette conclusion ne porte pas sur toutes les stratégies Hyperliquid.

Le diagnostic distingue désormais deux problèmes : un raccord incomplet entre
snapshot WebSocket et premiers diffs, réparable historiquement par REST ; et
une fraîcheur incompatible avec notre exposition maker, y compris sur le flux
natif. Augmenter le capital ne corrige aucun des deux.

## Expérience réalisée

[Protocole](PROTOCOL.md) et [enregistrement préalable](registration.json).
Depuis le même processus sur le serveur, abonnement simultané aux carnets
YES/NO natifs fast et L4 0xArchive. Deux témoins de 60 s : BTC 1896 à partir
de 08:09:22.508 UTC, puis ETH 1897 à partir de 08:10:24.148 UTC. Échéance des
outcomes le 8 septembre à 06:00 UTC ; ils sont sélectionnés dans les métadonnées,
sans activer leur qualification de trading. Aucun ordre envoyé.

| Mesure | BTC | ETH |
|---|---:|---:|
| Carnets natifs reçus, YES et NO | 222 | 222 |
| Événements L4 reçus | 75 | 93 |
| Âge natif min. / médian / P95 | 332 / 419 / 613 ms | 322 / 391 / 493 ms |
| Âge L4 min. / médian / P95 | 474 / 531 / 1 986 ms | 471 / 509 / 562 ms |
| Carnets natifs admissibles à 100 ms | 0 | 0 |
| Événements L4 sous 100 ms | 0 | 0 |
| Fraîcheur native à 500 ms, temps cumulé des deux coins | 13,5 % | 19,1 % |
| Fenêtres natives entièrement fraîches sur 1 350 ms | 0 / 216 | 0 / 216 |

Le budget inchangé est `âge + placement 350 ms + incertitude 50 ms ≤ 500 ms`.
Les 350 ms sont une hypothèse, pas une mesure d’ordre. Les fenêtres de
1 350 ms couvrent TTL 1 000 ms + annulation hypothétique 350 ms ; le contrôle
de fraîcheur ne suppose aucun fill. Elles se chevauchent et ne constituent
pas 432 essais indépendants. La couverture est du temps cumulé par coin,
pas une disponibilité du portefeuille.

Les chiffres séparent explicitement âge des événements et âge du carnet natif.
Ils ne mesurent pas la latence de placement, d’annulation ou de confirmation
d’un ordre. Le seul test de 100 ms n’expliquerait donc pas toute la viabilité ;
l’absence de fenêtre d’exposition fraîche fournit ici un second rejet.

## Raccord initial défectueux : preuve et réparation

Le premier diff exploitable de chaque témoin supprime un ordre absent du
snapshot WebSocket. L’historique REST confirme sa création entre le dernier
bloc du snapshot et le premier bloc reçu :

| Coin | Bloc du snapshot | Création manquante | Première suppression reçue |
|---|---:|---:|---:|
| BTC YES `#18960` | 1 138 656 146 | 1 138 656 180 | 1 138 656 181 |
| ETH NO `#18971` | 1 138 657 018 | 1 138 657 064 | 1 138 657 172 |

[Preuve détaillée](startup_gap.json). Aucun gap explicite n’est signalé dans
les captures. Le reconstructeur bloque sur l’ordre inconnu, sans ignorer sa
suppression ni créer un ordre fictif. Cela démontre un raccord initial
incomplet dans ces captures, pas une perte permanente sur tous les flux.

Un contrôle borné de **14 requêtes REST, 62 391 octets**, récupère six paires
de checkpoints et deux pages de diffs. En remplaçant uniquement la base du
rejeu offline par un checkpoint REST daté et en excluant les diffs antérieurs
ou égaux à son bloc :

- **183/183 comparaisons exactes** avec le carnet natif YES : 101 BTC, 82 ETH ;
  cinq niveaux de chaque côté, prix, taille et nombre d’ordres.
- **6/6 comparaisons REST indépendantes du rejeu WebSocket** concordantes,
  aux indices natifs YES 0, 50 et 100 de chaque témoin.
- 98 blocs physiques fermés par observation d’un bloc ultérieur sur le même
  coin : BTC 21/21 et ETH 5/51. Les premiers intervalles non qualifiables et
  les derniers blocs sans successeur sont exclus.

La source REST est récupérée après la capture : cette réparation utilise
des informations qui n’étaient pas disponibles lors des décisions passées.
Elle ne répare donc pas rétroactivement la causalité d’une exécution live.
Les horloges originales de réception des diffs sont conservées.

La profondeur peut rester inchangée malgré des événements anciens. Sur les
états comparables, le dernier événement nécessaire au carnet physique est
reçu après le carnet natif dans 8 cas BTC et 13 cas ETH. Ce compteur ne mesure
pas exclusivement les changements de meilleur prix. Attendre un bloc suivant
sur les deux coins ajoute parfois plusieurs secondes lorsque l’un est calme :
ce délai conservateur de confirmation ne doit pas être présenté comme la
latence réseau du fournisseur.

## Ce qui est établi et ce qui ne l’est pas

L’ordre serveur par coin permet ce rejeu après base REST. L’absence d’un champ
`seq` n’est pas à elle seule une erreur ; l’ordinal local utilisé par le
reconstructeur est un détail d’application, jamais une séquence exchange.
La détection indépendante de toutes les omissions, la priorité entre carnets
YES/NO et l’attribution des fills maker restent non qualifiées. Le natif ne
fournit pas de bloc dans ces messages ; la comparaison utilise ses timestamps.

Le contrat fournisseur décrit l’ordre des diffs et la reconstruction depuis
un checkpoint dans [WebSocket L4](https://docs.0xarchive.io/websocket/l4-orderbook),
ainsi que les événements de gap dans [le schéma](https://docs.0xarchive.io/websocket/schema).
Le format natif est documenté dans
[les abonnements Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions).
Les conclusions chiffrées viennent des captures, pas de promesses fournisseur.

## Livraison et limites

Réutilisation du stockage append-only, des événements immuables, des checksums,
du témoin L4 et du reconstructeur HyperBot2. Ajouts : capture simultanée,
fermeture conservatrice des blocs et analyse offline, avec option explicite
de réparation historique REST. **174 tests passent**, lint/format et mypy
sur 45 modules passent. Les tests couvrent notamment le bloc incomplet, le
gap, la régression temporelle, l’ordre inconnu et le remove sans champ taille.

Le premier lancement Docker a échoué avant toute capture sur un montage
imbriqué en lecture seule. Un bundle autonome a corrigé le montage ; l’erreur
est conservée dans `server_capture_execution.json`. Les premiers rapports
d’analyse conservent aussi l’erreur d’adaptation `sz` sur les suppressions,
corrigée et testée, puis le véritable blocage d’ordre inconnu. Les rapports
finaux sont [BTC](final_1896.json) et [ETH](final_1897.json) ; les résultats
intermédiaires ne sont pas écrasés.

[Installation finale](server_install.json) séparée sous `/opt/hyperbot2/research`.
Le runtime `b44a0baa421ac7f2` reste inchangé. Aucun conteneur actif après les
tests. Les raws restent hors Git, localement dans
`data/maker_final_2026-09-07/` et sur le serveur dans
`/opt/hyperbot2/shared/data/maker-final-2026-09-07-{1896,1897}`. Les clés ne
figurent pas dans les commandes, rapports ou manifestes.

Reproduction des chiffres, sans réseau :

```bash
uv run python scripts/analyze_maker_pair.py \
  --capture data/maker_final_2026-09-07/server/maker-final-2026-09-07-1896 \
  --historical-rest-manifest data/maker_final_2026-09-07/rest/manifest.json \
  --output data/maker-btc-recheck.json
```

Remplacer 1896 par 1897 pour ETH. Omettre l’option REST pour reproduire le
blocage initial. Les répertoires de capture et les rapports de sortie existants
ne sont jamais écrasés. Les historiques REST restent B ; aucun frais, fill
ou résultat économique n’est validé par ce diagnostic.

## Décision opérationnelle

Clôturer ce diagnostic et suspendre le maker HIP-4 dans les conditions
actuelles. Un nouveau test identique ne modifierait pas la décision sans
changement concret : raccord snapshot/diffs fiable et données exploitables
pendant l’exposition, ou nouvelle conception de stratégie avec son propre
protocole de validation. Ne pas baisser les seuils pour obtenir un GO.

Un autre transport pourrait changer le résultat, mais son coût, sa couverture
HIP-4 et sa fraîcheur devraient être démontrés avant engagement. Aucun achat
ni nouvelle collecte permanente n’est nécessaire pour terminer ce diagnostic.
La recherche d’une stratégie rentable peut continuer séparément ; la cible de
+30 % mensuels n’est pas validée.
