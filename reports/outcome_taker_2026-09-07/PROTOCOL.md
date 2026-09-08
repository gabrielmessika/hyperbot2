# Outcomes taker : protocole enregistré le 7 septembre 2026

Hypothèse : le prix demandé sur un binaire journalier peut sous-évaluer une
probabilité prudente, sans exiger de priorité maker. Réutiliser le benchmark
digital Hyperbot2, les bougies natives existantes et les carnets legacy ; aucun
achat, aucun ordre. Les observations de résultat paper ne servent pas de labels.

Enregistrement après inventaire des carnets et trois sondes de résolution
(111, 762, 1715), avant calcul des signaux/PnL. Ces trois contrats sont exclus
du test économique. L'historique du sous-jacent a déjà été utilisé dans d'autres
recherches : ce test n'est pas un holdout global vierge.

- Source principale : snapshot original Nautilus de TRIDENT, déjà importé par
  Hyperbot, SHA-256 e23544528c2e64b6c72ae42e93458e4ed6a002993aa4808e75ce933cb435d959.
  Copier seulement un extrait déterministe checksumé, conserver les deux
  horloges `ts_event` et `ts_init`. BTC, ETH, SOL, HYPE, contrats quotidiens.
- Une décision par contrat à 12:00:05 UTC la veille de l'expiration 06:00 UTC.
  Carnet le plus récent effectivement reçu avant la décision, âgé au plus de
  60 s sur chacune des deux horloges. Aucun remplacement par un carnet futur.
- Référence : dernière clôture horaire native terminée à 12:00 UTC ; hypothèse
  de disponibilité à +5 s, sans preuve de réception historique. Volatilité
  empirique des 168 rendements horaires antérieurs, sans calibration ni drift.
  Le cours perp est un proxy du mark de settlement, limitation explicite.
- Probabilité prudente de chaque côté : minimum des probabilités du benchmark
  sous volatilité ×0,75 /1 /1,25, moins 0,03 absolu. Acheter le côté offrant
  au moins 0,05 de marge absolue après provision settlement de 0,2 % ; prix
  demandé entre 0,15 et 0,85. Un seul côté, meilleur écart, égalité YES.
- Exécution exploratoire : premier carnet reçu après décision +1 s, avant
  décision +60 s ; prix retenu = pire des asks décision/exécution. Quantité
  entière arrondie au-dessus pour atteindre 10 $ de notional, dépense ≤11 $,
  disponible au meilleur ask dans les deux observations. Maximum 10 % de la
  taille visible, pas de consommation supposée de niveaux non conservés.
  Un manque de profondeur ou une dérive au-delà de la limite annule l'entrée.
- Stress coûts : +0,01 absolu au prix d'achat et 0,2 % sur le payout ; base
  sans supplément de prix et 0,07 % sur le payout. Aucune commission d'ouverture,
  conformément à la mécanique documentée ; taux choisis comme scénarios de
  recherche, pas comme attestation des frais historiques du compte.
- Retard : même signal figé, premier carnet reçu après décision +60 s, avant
  +120 s, quantité et limite décisionnelles conservées. Aucune sélection par
  résultat futur. Conserver à la résolution officielle `settledOutcome`.
- Au plus 44 $ immobilisés simultanément pour 1 000 $ de capital, sans levier.
  Si absence de label officiel, exclure et compter ; aucun label imputé.
- Séparer ancien (expiration avant 15 juin) et validation (à partir du 15 juin).
  Publier chaque actif, refus, nombres de dates indépendantes, PnL de base,
  stress/retard et IC 99 % bootstrap par date, 10 000 tirages, seed 1709.
  Pas d'optimisation après résultats ni de multiplication des heures testées.
- Candidat digne d'une réplication seulement si ≥30 dates de trades, ancien et
  validation positifs, stress et retard positifs, IC inférieur >0, pas plus de
  50 % du profit positif provenant d'un seul actif, et ≥30 $/30 jours après
  une hypothèse explicite de 20 $/mois d'infrastructure au sizing enregistré.
  Ce seuil constitue un filtre économique, pas l'objectif initial +30 %/mois.
  Les datasets legacy et les fills simulés ne donnent jamais seuls un GO live.

Références : [benchmark de marché externe, hypothèse seulement](https://arrakis.finance/blog/hip-4),
[mécanique officielle des frais](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees),
[endpoint de résolution](https://www.quicknode.com/docs/hyperliquid/info-endpoints/settledOutcome).
La publication Arrakis compare des probabilités et markouts ; elle ne valide
pas notre rentabilité nette ni notre exécution.
