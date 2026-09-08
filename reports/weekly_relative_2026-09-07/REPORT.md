# Rotation hebdomadaire : petit gain, piste suspendue

La règle long/short enregistrée gagne **81,62 $ sur 180 jours** avec 1 000 $
et un plafond brut d'entrée de 0,5x, frais et funding inclus, sans infrastructure.
Cela représente **1,32 % mensuel composé équivalent**, pas une prévision.
Ce résultat reste loin de l'objectif de recherche de 15–20 % ; augmenter les
tailles testées dépasse l'enveloppe de risque de 20 %. Aucun GO.

## Expérience et coûts

18 altcoins, données natives complètes du 10 mars au 6 septembre 2026 exclusif,
déjà disponibles localement. Chaque lundi, classement sur sept jours en excluant
la dernière journée, achat des trois premiers et vente des trois derniers.
23 paniers hebdomadaires, 138 cycles à 0,5x, première entrée le 23 mars et
dernière sortie le 31 août. Les jours de chauffe et la fin inactive restent
inclus dans les 180 jours. Même règle dans tous les scénarios.

Quantités arrondies, minimum 10 $, capital partagé, positions et funding
timestampés, frais/slippage centraux 4,5/2 bps par côté ; stress 9/5.
Une fermeture/réouverture est facturée chaque semaine, même pour un actif
conservé. Simulation horaire, exécution open+60 secondes au prix open supposé,
oracle de funding approché par l'open. Les fills réels restent non qualifiés.

## Résultats à 0,5x

| Scénario | Net, infra 0 $ | Net, infra hypothétique 20 $/30 j |
|---|---:|---:|
| Central | +81,62 $ | −38,37 $ |
| Coûts renforcés | +62,03 $ | −57,10 $ |
| Retard d'une heure | +81,98 $ | −39,20 $ |
| Funding adverse | +42,80 $ | −72,83 $ |
| Contrôle zéro coût de trading | +97,09 $ | −23,11 $ |

Les 20 $ sont une sensibilité hypothétique, aucune dépense engagée.
Sans infrastructure, le drawdown central observé est 9,02 %, son enveloppe OHLC
15,02 %. Les quatre scénarios payants passent le filtre préliminaire de
positivité et de risque sans infrastructure. Le statut brut
`WEEKLY_RESEARCH_CANDIDATE_UNQUALIFIED` signifie seulement ce passage ; la revue
économique conclut `POSITIVE_SMALL_RETURN_RESEARCH_SUSPENDED`.

À 1x, le net central est +155,14 $, mais l'enveloppe atteint 28,67 %.
À 1,5x, +110,82 $, arrêt après 48 cycles, drawdown observé 20,23 % et
enveloppe 22,27 %. Les dépassements sont conservés, sans écrêtage ni reprise.
Le plafond d'entrée ne maintient pas un levier constant : à 0,5x, le ratio brut
observé monte à 0,783 avec les variations des prix. Aucun problème de marge
simulé, sous les hypothèses de marge enregistrées ; ce n'est pas une
validation de liquidation native.

## Concentration et comparaison

À 0,5x sans infrastructure : cinq périodes calendaires positives, août négatif
(−26,91 $), septembre neutre ; mars et septembre sont partiels. Le mois rouge
n'est pas un motif de rejet. Le compte reste sous son sommet pendant 92,67 jours
jusqu'à la fin. Pire cycle −90,29 $. ENA contribue −137,12 $, UNI −58,39 $,
WLD +86,17 $, PUMP +67,67 $, ZEC +63,74 $. Aucun perdant retiré après calcul.

Le comparateur long des 18 actifs, entré au même premier lundi puis conservé
jusqu'au dernier open, gagne +379,75 $ à 0,5x, enveloppe 16,43 %. Il possède
une exposition différente et n'est pas promu opportunément. Ses dates diffèrent
des comparateurs d'autres études : ne pas mélanger ces baselines.

## Limites et livraison

Univers courant et période déjà examinée : pas de holdout. Six mois ne valident
pas douze mois. Équilibrage en dollars à l'entrée ne signifie pas neutralité
en bêta. L'enveloppe OHLC peut surestimer un chemin simultané ; l'observation
horaire peut manquer un mouvement rapide. Aucun rendement garanti.

63 artefacts reproduits exactement ; 257 tests, lint/format (245 fichiers) et
mypy (66 sources) passent. Voir `PROTOCOL.md`, `summary.json`, `review.json`
et `reproduction.json`. Aucun nouvel appel de données, ordre, achat, changement
de service ou de serveur. Recherche active : qualification des sessions et
oracles des actions coréennes avant un éventuel test d'ouverture.
