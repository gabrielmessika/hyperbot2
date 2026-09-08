# Écarts nocturnes : les deux règles échouent

112 dates possibles du mardi au vendredi sur les sept historiques d'actions
HIP-3 déjà acquis. Entrée 08:00 New York si variation nocturne >=1 %, sortie
10:00, après ouverture régulière. Deux segments et deux directions enregistrés
avant calcul, aucune dépense ou acquisition supplémentaire.

| Direction / segment | N / dates actives | Net moyen | Stress coûts | Retard 1 h | PF | IC 97,5 % |
|---|---:|---:|---:|---:|---:|---|
| Fade, ancien 12 février–1 juin | 174 / 50 | −52,46 bps | −76,41 | −56,74 | 0,53 | [−94,52 ; −5,63] |
| Fade, validation 1 juin–6 septembre | 170 / 50 | −53,14 bps | −77,13 | −57,08 | 0,59 | [−116,99 ; +58,10] |
| Follow, ancien | 174 / 50 | +8,55 bps | −15,39 | +12,75 | 1,11 | [−38,22 ; +50,48] |
| Follow, validation | 170 / 50 | +9,16 bps | −14,83 | +13,09 | 1,10 | [−102,07 ; +73,03] |

Le fade perd même sans frais/funding : −30,57 et −31,16 bps. Le follow montre
une petite moyenne positive après coûts de base, mais elle est absorbée par le
stress de coûts et n'est pas statistiquement étayée. Les retards d'entrée seule
et de sortie seule sont conservés comme diagnostics ; ils ne remplacent pas
le stress prévu et ne servent pas à choisir un nouvel horaire gagnant.

**HYPOTHESIS_NOT_CONFIRMED** pour les deux directions. Aucun paramètre changé
entre ancien et validation, aucun ticker sélectionné après résultat. Les
fenêtres étaient réservées à cette nouvelle hypothèse ; les historiques ont
déjà servi à la recherche de week-end et ne sont pas un holdout global vierge.

Reproduction : `rtk proxy uv run python scripts/investigate_overnight_repricing.py
--output <nouveau_dossier>`. Le moteur économique, le chargeur et les frais
reprennent ceux du week-end. Tests du calendrier : lundi/fériés exclus, close
précédent présent, durée de deux heures et distinction signal/entrée garanties.
Raw et événements complets sous `data/overnight_repricing_2026-09-07/run1/`.

Limites : prix de référence interne au perp, pas juste valeur actions ; frais
historiques et oracle non qualifiés ; opens hypothétiques ; pas de simulation
de portefeuille, marge, corporate actions ou garantie de rendement mensuel.
