# Fin d'échéance : borne économique, sans stratégie ni signal

Enregistrement avant calcul. Utiliser l'archive Nautilus originale déjà
checksumée et l'univers de 115 contrats de l'extraction outcomes précédente.
Réutiliser leurs labels officiels natifs, y compris les deux sondes exclues
du test causal précédent : ici la connaissance de la résolution future est
**volontaire**, uniquement pour construire une borne optimiste.

Calculs distincts, aucun des deux ne peut justifier un GO :

1. **Point fixe à cinq minutes** : dernier carnet reçu avant expiry−300 s,
   avec âge événement et réception ≤60 s, acheter seulement le côté gagnant
   connu a posteriori. Un prix par contrat. Allocation maximale 1 000 $ par
   date d'expiration, sans réinvestissement ; répartition optimiste vers les
   meilleurs rendements. Publier avec 100 % puis 10 % du meilleur ask visible,
   unités fractionnaires permises, aucun minimum d'ordre. Ignorer files,
   latence et concurrence : c'est une relaxation optimiste du problème réel.
2. **Borne de prix sur les six dernières minutes** : meilleur ask du côté
   gagnant observé entre expiry−360 s et expiry−1 s, reçu avant l'expiration,
   âgé au plus de 60 s. Avec connaissance parfaite du gagnant et du meilleur
   instant, supposer une profondeur infinie à ce meilleur prix et allouer tout
   le capital au meilleur contrat de la date. Une borne volontairement très
   généreuse pour les prix observés, sans prétention sur les intervalles absents.

Scénarios : aucun frais, puis 7 bps sur le payout seulement ; aucune commission
d'ouverture. Capital 1 000 $ non cumulé entre marchés de même échéance. Pas de
short de tokens ni de hedge. Conserver jusqu'à la résolution officielle.
L'enveloppe calendaire entière sert à convertir en proxy /30 jours ; signaler
les dates absentes et carnets non utilisables. Déduire séparément l'hypothèse
20 $/mois d'infrastructure. Cible utilisateur acceptable 150–200 $ nets/mois.

Si même la borne de prix est inférieure à 150 $/30 jours, suspendre cette
classe d'achat-conservation en fin d'échéance sur les données observées.
Si elle dépasse ce montant, cela démontre seulement qu'une borne triviale ne
suffit pas à rejeter : il reste à qualifier prix du sous-jacent, causalité,
risque de résolution, profondeur et reproductibilité d'un véritable signal.

Ne pas utiliser les probabilités, scores ou décisions legacy comme vérités.
Les deux fichiers `short_expiry_features.csv` se chevauchent largement et ne
multiplient pas le nombre de contrats indépendants. Aucun téléchargement,
nouvel abonnement, service, ordre ni trading live dans ce diagnostic.
