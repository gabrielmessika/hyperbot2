# Audit de données — liquidations BTC/ETH

7 septembre 2026. Audit initial sans lecture des rendements futurs : routes
core perp BTC/ETH uniquement, une journée fixe du 5 au 6 septembre UTC pour
schéma/accès ; liquidations brutes, volumes horaires, open interest horaire,
couverture fournisseur. La journée de schéma ne sera pas une validation OOS.

Budget initial huit requêtes ; plafond de campagne 100 requêtes, 50 Mo,
30 minutes d’acquisition. La clé existante est lue hors Git et transmise par
stdin/en-tête, sans achat ni modification serveur. Toute pagination incomplète,
direction ambiguë ou couverture inconnue sera explicitée. Ne pas assimiler
une absence d’enregistrement à zéro liquidation sans preuve appropriée.

Après vérification du schéma, fixer la période et le protocole d’événements
avant téléchargement large ou lecture de rendements. Distinguer liquidations
de positions longues, courtes et lignes de contrepartie ; vérifier les
agrégats avec des événements bruts. Aucun signal fondé uniquement sur la
forme d’une bougie ne sera appelé liquidation. L’OI en contrats et sa valeur
en dollars ne sont pas interchangeables.
