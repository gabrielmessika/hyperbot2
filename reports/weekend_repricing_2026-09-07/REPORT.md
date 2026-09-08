# Retour des mouvements du week-end : positif mais non validé

206 jours natifs, du 12 février au 6 septembre 2026 UTC exclusif. Cinq marchés
initialement fixés : TSLA/NVDA/HOOD/META/AMZN sur xyz. 55 requêtes publiques,
24 720 bougies et autant de funding horaires ; aucune dépense. Grilles complètes,
jours fériés et changement d'heure New York contrôlés. 24 week-ends admissibles.

| Expérience fade | Événements / week-ends actifs | Net moyen | Stress coûts | Retard 1 h | PF |
|---|---:|---:|---:|---:|---:|
| Cinq marchés initiaux | 19 / 11 | +118,47 bps | +94,46 bps | +135,68 bps | 2,89 |
| Réplication COIN/MSTR | 25 / 15 | +66,04 bps | +41,87 bps | −4,69 bps | 1,51 |

Entrée dimanche 12:00 New York contre un mouvement >=1 % depuis le vendredi
16:00, sortie lundi 10:00. Frais base 9 bps/côté, stress 18 ; slippage 2/5.
Le contrôle follow est négatif en base dans les deux expériences (−162,49 et
−110,32 bps). Les deux sens avaient été déclarés avant chaque calcul.

L'original reste positif après retrait du meilleur événement, mais HOOD produit
2 073,53 des 2 250,88 bps cumulés. Seulement quatre des sept blocs de 30 j sont
positifs, contre cinq requis. Pas d'intervalle de confiance présenté sur seulement
11 week-ends actifs. La réplication a été enregistrée après ce constat de
concentration, avant lecture des nouveaux prix ; elle ne constitue pas une
promotion acquise par les gates initiales. Elle garde COIN et MSTR positifs
séparément en base, mais devient négative avec le décalage d'une heure et ne
dispose que de 15 week-ends actifs. Les critères échouent dans les deux cas.

Le retard teste la persistance face à un changement d'horaire, pas une estimation
de latence réseau. Il décale aussi la sortie après l'ouverture américaine. Cet
échec n'établit pas une impossibilité d'exécuter à 10:00 ; il laisse la robustesse
de la règle non démontrée. **HYPOTHESIS_NOT_CONFIRMED**, aucun GO ou ordre réel.

## Fréquence et capital : ne pas confondre bps par trade et rendement mensuel

Diagnostic descriptif, sans agréger les études pour remplacer la réplication :
44 événements sur 18 week-ends distincts, jusqu'à sept signaux simultanés.
À notionnel constant 50 $ par événement, somme théorique nette de trading
19,51 $ sur 206 jours, environ 2,84 $ par 30 j avant infrastructure.
En attribuant fictivement 1 000 $ de notionnel TOTAL par week-end, partagé
également entre les signaux, cette somme serait 90,39 $, soit environ 13,16 $
par 30 j avant infrastructure. Il ne faut pas attribuer 1 000 $ à chaque signal
simultané et présenter ce résultat comme un portefeuille sans levier.

Ces illustrations ne simulent ni stops, equity intermédiaire, arrondis ni
réservations de risque, et ne constituent pas des rendements réalisables ou une
borne garantie. Elles montrent que même le signal positif ne démontre pas une
capacité de +300 $/mois avec 1 000 $. À elles seules, elles ne couvrent pas le
budget hypothétique d'infrastructure de 20 $/mois utilisé précédemment.

Le mécanisme reste une observation intéressante mais trop rare pour être retenu
comme bot dédié dans les conditions étudiées. L'expérience suivante, distincte,
teste les écarts nocturnes du mardi au vendredi sur les mêmes données, sans
réduire le seuil ou déplacer les horaires du week-end.

Reproduction : `scripts/investigate_weekend_repricing.py --output <nouveau>` et
`scripts/replicate_weekend_repricing.py --raw
data/weekend_repricing_2026-09-07/replication_history --output <autre>`, via
`rtk proxy uv run python`. Le wrapper réutilise le moteur sans copier la règle ;
`replication.json` identifie explicitement l'univers, le nouveau protocole et
les hashes. Historiques bruts ignorés Git, résumés checksumés dans ce dossier.

Sources : [calendrier NYSE](https://www.nyse.com/publicdocs/nyse/ICE_NYSE_2026_Yearly_Trading_Calendar.pdf),
[frais HIP-3](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees).
Frais historiques, événements corporate, oracle et fills restent non qualifiés.
