# Écarts nocturnes avant ouverture américaine : protocole figé

Nouvelle hypothèse, issue du diagnostic des week-ends mais portant sur des
fenêtres distinctes. Univers des sept historiques déjà acquis, sans sélection :
xyz:TSLA/NVDA/HOOD/META/AMZN/COIN/MSTR. Aucun téléchargement supplémentaire.
Les prix ont servi aux études précédentes ; ces rendements nocturnes précis
n'ont pas encore été évalués. Il ne s'agit pas d'un holdout global vierge.

Du mardi au vendredi, hors férié américain ce jour ou la veille : comparer le
close du perp sur la bougie précédente 15:00–16:00 New York au close de la
bougie courante 07:00–08:00. Variation absolue >=1 % : prendre le sens opposé
(fade), entrée open 08:00, sortie open 10:00, après l'ouverture régulière.
Contrôle directionnel follow enregistré d'avance. Aucune borne haute sur le
gap ni exclusion de news a posteriori. Lundi exclu pour séparer ce test des
week-ends déjà étudiés. Heure d'été et calendrier natifs du module existant.

Deux segments évalués séparément avec règles identiques : 12 février–1 juin
2026 UTC exclusif (ancien), 1 juin–6 septembre (validation interne à cette
hypothèse). Aucun réglage entre les deux, aucune agrégation pour masquer un
échec. Les deux scénarios doivent réussir dans les deux segments pour être
retenus, chaque direction ayant sa propre décision.

Réutiliser les frais HIP-3 9 bps/côté (stress 18), slippage 2 (stress 5), funding
horaire signé et adverse, contrôle sans coûts/funding. Retard principal :
entrée/sortie 1 h, conservation de la durée de 2 h. Deux diagnostics descriptifs
supplémentaires séparent retard d'entrée seul et de sortie seule ; ils ne peuvent
remplacer le stress principal s'il échoue. Aucun résultat ne qualifie à lui seul
les frais historiques, l'oracle ou l'exécution sur un prix d'open.

Gates dans chaque segment : >=30 événements et >=20 dates actives ; net positif
en base/coûts/retard principal/funding adverse ; PF>1,2 ; au moins trois blocs
de 30 j positifs ; somme positive après retrait du meilleur événement ; IC 97,5 %
de moyenne net positif par bootstrap de blocs de 7 jours calendrier, 5 000
réplications, deux directions. La correction locale n'efface ni la sélection
de la famille ni les recherches antérieures. Pas de modification d'horaire,
seuil, ticker ou direction en fonction des résultats.

Si passage : vérifier dépendance au marché et aux earnings, allocation/risque
avec 1 000 $, frais, tailles, données fines gratuites et stabilité prospective.
Si échec : conserver les résultats et suspendre sans prétendre avoir obtenu GO.
