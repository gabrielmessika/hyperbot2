# Chocs de rendement couverts par BTC : coûts supérieurs au gain brut

**Hypothèse non confirmée.** Sur 504 événements et 148 dates d'entrée, le retour
à la moyenne sur six heures donne **+9,25 bps avant tout coût**, puis
**−3,62 bps nets moyens par dollar de panier brut**. La règle est suspendue ;
aucun portefeuille n'est présenté comme rentable à partir de ce résultat.

## Hypothèse et données

[Protocole enregistré](PROTOCOL.md) après l'échec du transfert funding, avant
calcul de cette règle. Le signal n'utilise pas le funding : il compare le
rendement de chaque altcoin à celui de BTC avec une régression sur 28 blocs
de six heures antérieurs, sans recouvrement entre ces blocs et en excluant le
dernier bloc qui sert au signal. Bêta, corrélation et sigma sont filtrés selon
les bornes enregistrées ; entrée à 3–6 sigmas, sens de correction.

**18 altcoins et BTC, 180 jours horaires natifs complets**, entièrement locaux.
Pas de nouvelle acquisition. Les prix ont déjà été examinés dans d'autres
recherches ; l'univers de volume courant garde un biais de sélection/survivance.
Les premières 175 heures servent au modèle et au signal ; la fin réserve le
prix de sortie de la sensibilité retardée à 24 h.

Bêta figé à l'entrée. Poids altcoin 1/(1+bêta), BTC bêta/(1+bêta), positions
opposées, quantités constantes. La somme des notionals du panier vaut un dollar
pour exprimer les rendements ; **ce n'est pas un ordre réel à un dollar** ni
une allocation du compte. Le hedge est approximatif, pas une neutralité garantie.

Entrée/exit open+60 s avec prix open hypothétique, funding timestampé, oracle
approché par l'open. Central 4,5 bps de frais et 2 de slippage par côté pour
chaque jambe ; stress 9/5. Réutilisation du modèle de hedge, des paiements,
du résumé et du bootstrap existants. Pas de maker ou de remplissage à la touche.

## Résultats

Moyennes en bps par événement, sur le notional **total** des deux jambes.

| Scénario | Principal 6 h | Descriptif 24 h |
|---|---:|---:|
| Central | **−3,62** | −28,80 |
| Coûts renforcés | −18,62 | −43,81 |
| Retard 1 h | −6,06 | −31,13 |
| Funding adverse | −4,64 | −32,64 |
| Sans aucun coût | +9,25 | −16,21 |

Le PF central six heures vaut **0,91**. Son intervalle descriptif à 95 %,
par blocs de sept jours et 5 000 tirages, est **[−16,59 ; +7,24] bps**. Il ne
démontre pas une moyenne nette positive et ne corrige pas toutes les recherches
antérieures. Le total sans le meilleur événement reste négatif. Le pire panier
perd 630,70 bps (6,31 % de son notional), sans qu'un risque de compte soit déduit.

Deux blocs de trente jours sont positifs et quatre négatifs. Leur couleur n'est
pas le veto : **le total net est négatif dans tous les scénarios payants**.
Quelques contributions d'actifs sont positives (notamment XMR et FARTCOIN) ;
elles ne sont pas utilisées pour choisir rétrospectivement un nouvel univers.
L'horizon descriptif 24 h échoue également, même sans coûts.

## Décision et suite

Statut `HYPOTHESIS_NOT_CONFIRMED`. Aucun GO, aucune extension en portefeuille,
aucune modification de seuil/horizon/actif pour sauver cette règle.
La prochaine hypothèse sera une rotation hebdomadaire long/short entre
altcoins forts et faibles, avec un horizon et une logique différents de la
correction d'un choc de six heures. Elle devra être enregistrée et utiliser
le même panel gratuit, avec allocation, frais, funding et risque de compte.

**254 tests passent**, lint/format 240 fichiers et mypy 65 sources passent.
Les nouveaux tests vérifient l'exclusion du bloc signal de l'entraînement,
l'absence d'effet des prix futurs et le refus d'un historique trop court.
Trois artefacts sont reproduits exactement : [preuve](reproduction.json).
Aucun achat, ordre, changement serveur ou redémarrage de service.
