# Chocs de volume : aucune règle retenue

Deux hypothèses enregistrées avant calcul sur 180 jours d'OHLCV natives,
BTC/ETH/SOL/HYPE ; 7 jours de chauffe. Aucun achat ni appel réseau.

| Règle, horizon principal 6 h | Événements | Net moyen (bps) | Coûts stressés | Retard 1 h | PF | IC 97,5 % du net |
|---|---:|---:|---:|---:|---:|---|
| Continuation après choc | 211 | −1,91 | −16,94 | −9,06 | 0,97 | [−33,14 ; +23,43] |
| Rejet par longue mèche | 146 | −11,53 | −26,54 | −41,43 | 0,84 | [−61,32 ; +35,62] |

Les rendements bruts sans frais/funding sont respectivement +11,26 et +1,46
bps : insuffisants après coûts. Trois blocs de 30 jours positifs sur six pour
chaque règle. Toutes les contributions par coin de la continuation deviennent
négatives sous coûts stressés. Le rejet est très sensible au retard d'entrée.

Le résultat secondaire à 24 h de continuation est positif (+25,55 bps nets),
mais il ne remplace pas l'horizon principal après observation. Ce n'est ni une
validation ni une raison de sélectionner ce paramètre sur ces mêmes données.
La famille est suspendue pour cette passe ; aucune simulation de rendement
mensuel ou de portefeuille n'est justifiée.

Reproduction : `rtk proxy uv run python scripts/investigate_volume_shocks.py
--output <nouveau_dossier>`. Entrées validées SHA-256, OHLCV et grilles complètes ;
protocole et enregistrement dans ce dossier, résumé `summary.json`, événements
complets sous `data/volume_shocks_2026-09-07/final/` (ignorés Git).

Limites : historique déjà exploré, univers restreint, volume en unités du coin,
prix de trade sans garantie d'exécution, funding valorisé avec proxy horaire.
Bootstrap temporel corrige seulement les deux hypothèses de cette famille ;
il n'efface pas les recherches précédentes. **HYPOTHESIS_NOT_CONFIRMED**.
