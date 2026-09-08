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
- Recherche : utiliser les données existantes ou gratuites, sans nouvelle dépense.
  L'utilisateur accepte aussi une stratégie visant +15 % ou +20 % nets par mois
  (150–200 $ pour 1 000 $) ; +30 % n'est plus un minimum obligatoire. Aucun de
  ces niveaux n'est une garantie ; les exigences de preuve et de risque restent.
  L'utilisateur envisage aussi une cible de +10 % nets mensuels : évaluer ce
  scénario économique (100 $ pour 1 000 $) sans relâcher les preuves ni le risque.
  L'utilisateur accepte des séances et mois perdants (par exemple huit mois
  gagnants sur douze), si le résultat global net est largement positif. Ne pas
  exiger chaque mois positif ni traiter la cible mensuelle comme un minimum
  garanti. Comparer rendement cumulé, drawdown, pertes extrêmes et récupération.
  Une prise de risque accrue est autorisée dans les simulations de recherche ;
  elle ne modifie pas les limites runtime/live. Après un premier plafond de
  drawdown à 20 %, l'utilisateur autorise une comparaison à **30 %** pour les
  simulations si l'espérance de gain augmente. Le plafond de recherche accepté
  est donc 30 % depuis le sommet (environ 300 $ sur un sommet de 1 000 $),
  avec comparaison conservée à 20 %. Inclure positions ouvertes et coûts
  dans la mesure ; une mesure aux seules sorties ne valide pas ce plafond.
  Une piste bloquée par un accès payant doit être suspendue au profit d'une autre
  hypothèse. Ne pas proposer un achat comme étape par défaut de l'exploration.
- Commandes : `rtk proxy uv sync`, `rtk proxy uv run pytest`,
  `rtk proxy uv run ruff check .`, `rtk proxy uv run mypy src`.
