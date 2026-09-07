# HyperBot2 — instructions de développement

Lire `/home/goldadm/.codex/RTK.md` et préfixer les commandes shell avec `rtk`.

- `STRATEGY_IMPLEMENTATION_PLAN.md` définit le candidat outcomes et la campagne.
  `HYPERBOT_FOUNDATION.md` est le snapshot des limites/gates héritées.
  `FOLLOW_UP.md` suit le développement réellement livré.
- Python 3.11+, package autonome `src/hyperbot2/`. Les sources HyperBot,
  TRIDENT et BOT05 sont en lecture seule ; aucun import runtime vers ces dépôts.
- Code et commentaires techniques en anglais, documentation en français.
- Modèles immuables, montants `Decimal`, raw append-only, provenance checksumée.
- Aucun client de signature, ordre exchange ou dépendance de trading live.
  `live_enabled=false`, `shadow_only=true`, `public_data_only=true` obligatoires.
- L’utilisateur a ensuite autorisé un exécutable HyperBot2 propre sur le serveur.
  Installation et validation publique bornée de HyperBot2 autorisées ; les anciens
  services restent arrêtés, le trading réel reste interdit.
- B/C servent à l’exploration et au modèle optimiste uniquement. Les modèles
  maker central/pessimiste exigent A, causalité, file et mécanique duale qualifiées.
- Frais/settlement/tick inconnus, donnée stale, gap ou divergence : fail-closed.
- Mettre à jour le suivi et tester proportionnellement chaque livraison.
- Commandes : `rtk proxy uv sync`, `rtk proxy uv run pytest`,
  `rtk proxy uv run ruff check .`, `rtk proxy uv run mypy src`.
