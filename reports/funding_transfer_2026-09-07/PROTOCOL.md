# Transférabilité antérieure du signal funding 72 h

Test enregistré avant acquisition et calcul des nouveaux rendements. Réutiliser
le signal et le portefeuille existants : continuation 72 h après normalisation
du funding, mêmes seuils, espacement 73 h, plafond **0,4x**, allocation partagée,
minimum 10 $, arrondis, funding, stress de coûts/retard et drawdown 20 %.
Aucune recherche supplémentaire de taille, de délai ou d'actif performant.

## Univers et couverture

Les 18 actifs du dernier univers hors CASHCAT. Celui-ci ne dispose que de
116 heures avant le 16 juillet dans la réponse native obtenue : ce test ne
prétend donc pas répliquer son historique. Son résultat 52 jours reste conservé.

Acquérir les prix horaires et financements **10 mars–16 juillet exclusif,
128 jours**. Univers de transfert : actifs avec couverture complète de ces
128 jours, sélection exclusivement selon les trous, avant tout PnL. Les actifs
incomplets seront documentés et exclus également des comparaisons récentes.
Aucune imputation ou raccourcissement de fenêtre pour sauver un résultat.
Si moins de cinq actifs sont complets, ne pas calculer ce portefeuille.

Le filtre de volume courant et de survivance persiste. Ce test vérifie une
transférabilité dans cet univers, pas un backtest d'univers historique parfait.

## Simulations figées

Trois fenêtres, dont les rendements ne s'additionnent pas :
- antérieure : 10 mars–16 juillet, 128 jours ;
- récente : 16 juillet–6 septembre, 52 jours, même univers de transfert ;
- continue : 10 mars–6 septembre, 180 jours, sans reset au 16 juillet.

Pour chaque fenêtre : funding 72 h, panier long conservé, panier long périodique
72 h tous les 73 h. Même moteur 0,4x, au plus un tiers par actif, arrondis natifs,
entrée/exit open+60 s hypothétique. Central, coûts renforcés, retard 1 h, funding
adverse, contrôle zéro coût ; infrastructure 0 et 20 $/30 jours hypothétiques.
Les comparateurs n'autorisent pas à sélectionner une autre stratégie a posteriori.

Juger le total net, le risque et la concentration sur **180 jours continus**, en
utilisant les segments pour décrire la stabilité. Un segment ou mois rouge ne
suffit pas à rejeter une règle globalement largement positive. Publier équivalent
mensuel géométrique, PnL, drawdown complet/enveloppe, arrêts, mois, contributions,
durée sous le sommet. Pas de projection garantie de 15–20 % mensuels.

Passage du filtre de transfert : quatre scénarios payants positifs sur la fenêtre
continue, enveloppe <=20 %, sans violation du stress de marge. Un passage à
faible rendement ne démontre pas l'objectif économique ; l'absence de CASHCAT
doit rester visible. En cas d'échec, suspendre la promotion du mécanisme général
et conserver le candidat récent comme épisode non généralisé, puis changer
d'hypothèse. Aucun GO obtenu par ce seul transfert.

## Acquisition gratuite bornée

Deux lots de neuf actifs, **144 appels maximum au total**, au plus 20 Mo,
72 appels/10 Mo par lot : une requête de bougies et sept pages de financement
au plus par actif. Appels séquentiels, espacés de trois secondes, sans clé.
Client public existant, raw append-only, manifestes et SHA-256. Aucun appel
d'ordre, achat, service relancé ou modification serveur.

Respecter les [limites publiques natives](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits.md).
Les sources et artefacts finaux seront vérifiés et reproduits offline.
