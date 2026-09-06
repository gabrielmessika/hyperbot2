# Reprise de HyperBot

Le [manifeste initial](hyperbot_source_manifest.json) enregistre les chemins,
SHA-256 exacts des sources, commit de référence et empreintes du premier port.
Les sources ont été lues depuis le worktree ; le hash de chaque fichier prime
sur le commit si ce worktree contenait des changements. Le code et les tests
sont copiés, sans lien mutable ni import du dépôt d’origine.

| Composants repris | Usage HyperBot2 et adaptations |
|---|---|
| `models`, `event_store`, `segmented_store` | Contrats immuables, stockage append-only, checksums, fsync et segments |
| `services/public_collector` | Collector public avec file de persistance, horloges, reconnexions, ACK ; ajout de `fast=true` explicite et refus d’un ACK dégradé |
| `replay/engine` | Moteur déterministe central/pessimiste/optimiste ; enveloppe outcomes ajoutée pour ALO, dualité et frais par opération |
| `risk/supervisor`, `execution/shadow` | Limites et arrêt dur conservés ; comptabilité cash/FIFO et réservations ajoutées dans `outcomes/ledger` |
| `legacy/*` | Adaptateurs, manifestes et politique A/B/C ; lecture à la demande des archives, pas de copie massive |
| `research/*` historique | Digital benchmark, calibration isotone, purge temporelle, journal ; PF corrigé au niveau des cycles et bootstrap par journée commune aux cryptos |
| `strategies/common` | Arrondis tick/lot et dimensionnement minimum réutilisés |
| `build_info` | Namespace/variable `HYPERBOT2_CODE_COMMIT` ; CLI avec empreinte exacte de l’arbre source même avant le premier commit |

82 tests d’origine passent dans le nouveau namespace. Les tests supplémentaires
exercent les nouveaux contrats et les adaptations ; voir le rapport de livraison.
Les anciens planners directionnels et leurs paramètres ne sont pas importés.
La présence d’un ancien module de recherche ne qualifie pas sa stratégie.

Les empreintes du code effectivement exécuté sont dans le `source_manifest.json`
de chaque run. Elles peuvent différer des empreintes du port initial ci-dessus.
