# Flux et carnet : test taker enregistré le 7 septembre

Hypothèse distincte des bougies horaires : un flux agressif unilatéral peut
continuer lorsqu'il est soutenu par le carnet, ou se retourner lorsqu'il est
absorbé. BTC/ETH/HYPE seulement ; aucune stratégie legacy importée.

Enregistrement après inventaire et lecture d'un segment de qualité, avant
calcul des signaux et markouts. Source : exports Hyperbot déjà locaux, segments
fermés checksumés et dédupliqués par chemin/SHA-256. Pas de téléchargement,
d'achat, d'ordre ou de relance. Le lecteur Hyperbot2 et son format de stockage
servent de référence ; conserver l'horloge de réception et les timestamps natifs.

- Pilotage : 16–17 août 2026. Si les deux règles ont un markout moyen négatif
  même sans frais à 5 minutes, arrêter cette famille sans traiter les autres
  jours. Sinon réplication fixe 25–27 août, sans changer règles ni horizons.
- Grille de décision : secondes UTC entières, uniquement données reçues
  strictement avant la seconde. BBO avec bid/ask positifs non croisés, âge
  événement et réception ≤2 s. Historique 60 s complet après début de fichier
  ou interruption de réception >10 s. Pas de réutilisation d'état entre jours.
- Trades dédupliqués par coin/tid ; éliminer ceux reçus >2 s après événement ou
  dans le futur. Sommes en notional sur les 60 s de réception précédentes.
  Minimum 30 transactions et 100 000 $ BTC/ETH, 50 000 $ HYPE.
- Déséquilibre du flux : (achats−ventes)/(achats+ventes), module ≥0,7.
  Déséquilibre BBO : (taille bid−taille ask)/(taille bid+taille ask).
  Spread ≤2 bps. Variation du mid sur 60 s mesurée sur deux BBO frais.
- Continuation : déséquilibre BBO dans le sens du flux ≥0,5 et variation du
  mid dans le même sens ≥5 bps. Acheter/vendre dans le sens du flux.
- Absorption : déséquilibre BBO opposé au flux ≥0,5 et variation du mid dans
  le sens du flux ≤2 bps (y compris opposée). Prendre le sens inverse du flux.
- Premier signal, puis espacement 30 minutes par actif/règle. Horizon principal
  5 minutes ; 30 minutes descriptif seulement, aucune sélection a posteriori.
- Prix d'entrée/sortie au BBO causal à décision +1 s /+301 s, puis +1801 s
  pour le descriptif. Exiger BBO frais ; acheter ask, vendre bid. On modélise
  le prix disponible à l'arrivée, pas un ordre au cours passé. Retard : +2 s
  pour entrée/sortie. Notional 50 $ par actif, sans levier ; quantité arrondie
  vers zéro (BTC 5, ETH 4, HYPE 2 décimales). ≤10 % de taille visible aux deux
  extrémités. Si quote/profondeur manquante, événement non évalué et compté,
  jamais supposé gagnant. Une sortie manquante empêche toute qualification.
- Frais 4,5 bps par côté ; supplément slippage 1 bp par côté. Stress : frais
  7 bps et slippage 3 bps par côté. Funding natif signé entre entrée et sortie.
  Publier aussi mid→mid sans frais comme diagnostic, pas comme résultat tradable.
- PnL, moyenne bps, gains/pertes, taux d'événements évaluables, sous-périodes,
  actifs et jours ; bootstrap par date (IC 99 %, 10 000 tirages seed 709).
  Revenu à 50 $ par signal puis soustraction hypothétique 20 $/mois infra.
  Zéro optimisation, pas de choix d'actif après résultat.
- Piste à poursuivre seulement si base/stress/retard positifs sur pilotage et
  réplication, ≥100 événements/≥5 jours, IC inférieur >0, aucun actif ne
  concentre >50 % des profits positifs, sorties ≥99 % évaluables, proxy mensuel
  après infra ≥30 $. Un résultat positif réclame ensuite une période plus longue
  et indépendante ; ces quelques jours ne suffisent jamais à un GO live.

Classification : données publiques Hyperbot A à l'origine, extrait de recherche
avec intégrité de fichier ; ce test n'atteste pas un replay complet des chaînes
de hash ni une absence de perte silencieuse côté exchange. Les gaps et refus
doivent rester visibles. Aucun signal maker ni modèle de file ne sont déduits.
