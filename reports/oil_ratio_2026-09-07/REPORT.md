# Brent/WTI : économie insuffisante hors roulement

**Hypothèse non confirmée.** À 1x de notional brut total, les 18 trades donnent
+8,20 $ avant tout coût, puis −2,54 $ après frais, slippage et funding sur
158 jours. Le résultat est trop faible même avant infrastructure et devient
plus négatif sous stress. Aucun GO, aucun achat ni trading réel.

## Qualification des contrats

Les [spécifications commodities](https://docs.trade.xyz/asset-directory/commodities.md)
décrivent des références issues de futures pour le pétrole. Le tableau actif
ne donne pas la même échéance à WTI et Brent : ce sont deux expositions liées,
pas deux représentations interchangeables d'un actif à livraison identique.
Le [calendrier de roulement](https://docs.trade.xyz/consolidated-resources/roll-schedules.md)
fournit des dates précises à partir d'avril 2026. Les pages diffèrent sur la
présentation des jours de pondération ; aucune correction historique de prix
n'est inventée pour résoudre cette ambiguïté.

Le [protocole enregistré](PROTOCOL.md) exclut largement les jours 4–17 de chaque
mois New York, y compris dans les 24 heures de calcul du signal. Entrées
uniquement en semaine de 09 h à 14 h, hors fériés US du projet. Cette exclusion
couvre les rouleaux publiés pour avril–août, sans prétendre certifier toute la
timeline oracle ou les horaires CME/ICE historiques. Le mécanisme
[d'oracle interne/externe](https://docs.trade.xyz/perp-mechanics/oracle-price.md)
reste une limite à qualifier avant exécution réelle. Trois pages officielles
sont archivées avec horodatage et checksum.

## Données et réutilisation

CL provient intégralement de l'historique local. Seul Brent est téléchargé :
**neuf requêtes publiques natives, 917 430 octets**, aucun credential, 3 816
bougies horaires et taux de funding sur le 31 mars–6 septembre exclusif.
Le 31 mars sert au calcul initial ; évaluation du 1er avril au 6 septembre,
soit **158 jours et 3 792 heures** communes sans trou ni volume nul.

348 heures d'entrée sont permises par le calendrier ; 934 frames disposent
à la fois d'une statistique utilisable et d'un historique hors zone de roll.
Le ratio log(Brent/WTI) utilise 24 heures antérieures, excluant la bougie signal,
sigma minimal 0,002 ; entrée entre deux et quatre sigmas. Le pétrole relativement cher
est vendu, l'autre acheté pour un montant équivalent avant arrondis. Moyenne
et sigma figés jusqu'à sortie ; durée maximale deux heures.

Le moteur or/argent est **paramétré**, pas recopié : actifs, lookback, durée et
calendrier d'entrée explicites. Les sorties/exportations pétrole sont libellées
Brent/WTI. Les valeurs par défaut de l'ancien test restent identiques.

Capital initial 1 000 $, plafonds bruts totaux 0,5x/1x/1,5x, arrondis natifs et
minimum 10 $ par jambe. Les arrêts de paire à 3 % et de compte à 20 % restent
observés chaque heure, avec sortie au prochain open et dépassements conservés.
Deux frais growth de 0,9 bp/côté, plus 2 bps de slippage central ; timeline
historique de frais incomplète, comme dans les autres tests HIP-3.

## Résultats sans coût d'infrastructure supplémentaire

| Plafond brut | Central | Coûts renforcés | Retard 1 h | Funding adverse | Aucun coût |
|---|---:|---:|---:|---:|---:|
| 0,5x | −1,26 $ | −8,21 $ | −6,02 $ | −1,37 $ | +4,08 $ |
| 1x | −2,54 $ | −16,38 $ | −12,04 $ | −2,75 $ | +8,20 $ |
| 1,5x | −3,81 $ | −24,55 $ | −18,08 $ | −4,14 $ | +12,30 $ |

18 trades par taille en central, 17 avec retard. Ces scénarios sont alternatifs,
pas cumulables. Les trois tailles centrales ont trois périodes calendaires
positives, deux négatives et une neutre ; septembre est partiel. Les mois rouges
ne sont pas un veto : la règle échoue sur son **total net** et son économie.

À 1x sans infra, drawdown horaire 1,11 %, enveloppe adverse OHLC 3,51 %,
maximum 136,25 jours sous le sommet, équivalent mensuel composé −0,05 %. Avec
20 $/30 jours d'infrastructure hypothétique débités dans le portefeuille,
le résultat central devient −107,77 $. Aucune dépense réelle n'est engagée.

Un faible drawdown n'est pas à lui seul un edge. Le gain brut de 8,20 $/158 jours
ne justifie pas de multiplier l'exposition pour viser 150–200 $ mensuels,
alors que le gain net est déjà négatif. Cette conclusion concerne cette règle
et ses exclusions, pas toutes les possibilités sur les marchés pétroliers.

## Preuves, limites et suite

**241 tests passent**, lint/format 216 fichiers et mypy 62 sources passent.
Tests supplémentaires : mapping des actifs, durée et calendrier paramétrés,
blackout touchant les entrées et le passé de calcul. Les 30 scénarios or/argent
et leur qualité sont reproduits à l'identique après le changement de moteur.
Les 32 artefacts pétrole sont eux aussi reproduits : [preuve](reproduction.json).

Les courbes incluent les positions ouvertes, frais et funding, mais utilisent
des opens/fills hypothétiques et des extrêmes OHLC indépendants. Elles ne
prouvent ni profondeur, ni marks natifs, ni prix de liquidation ou chemin
intrahoraire. Cinq mois complets ne permettent pas de valider douze mois.
Aucun ancien bot ou dépôt modifié, aucune configuration serveur ou ordre.

Décision : `HYPOTHESIS_NOT_CONFIRMED`, règle suspendue. Recherche globale active.
Le prochain lot change de mécanisme : qualifier les épisodes de financement
extrême dans les archives natives déjà disponibles et leur comportement de prix,
avant d'enregistrer un test de normalisation. Ne pas essayer un autre simple
ratio de prix pour contourner les échecs conservés.
