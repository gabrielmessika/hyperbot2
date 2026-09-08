# Portefeuille partagé à 50/50, risque global 30 %

La qualification quotidienne trouve une corrélation cassures/rotation proche
de zéro dans les quatre scénarios payants. Cette observation sélectionnée
justifie un test, pas une promotion. Aucun poids ni paramètre de signal optimisé.

## Capital et positions

Panel natif complet **14 février–6 septembre 2026 exclusif**, 204 jours,
18 actifs identiques. Un seul compte de recherche de **1 000 $**. Répartition
fixe **50 % du budget d'exposition pour chaque mécanisme**, sur l'equity globale
courante. Pas de prêt automatique du budget d'un mécanisme inactif à l'autre.
Cap brut global d'entrée préenregistré : **0,5x /1x /1,5x /2x** ; dernier niveau
compatible avec le levier de configuration fixe 2 sous réserve des frais.
Pas de hausse de taille en réponse aux pertes.

Signaux inchangés : cassure avec volume, chauffe193/espacement25/détention24 h ;
rotation du lundi sur sept jours hors dernière journée, trois longs et trois
shorts, détention168 h. Les budgets, minimums et arrondis peuvent refuser des
entrées ; conserver ces refus. Plafond par actif et mécanisme : un tiers du
budget du mécanisme lors de l'entrée. Capital, frais et funding partagés.

Les positions sont suivies séparément par mécanisme dans un **registre virtuel**
sur le même sous-jacent. Cela ne représente pas deux comptes capitalisés à
1 000 $. Gains/pertes et funding signés s'additionnent sur l'unique cash.
Frais/slippage de chaque jambe sont facturés intégralement, même lorsqu'une
exécution nette pourrait économiser un trade. Budget brut, marge et enveloppe
OHLC comptent les deux positions avant compensation : choix conservateur,
pouvant surestimer un risque simultané quand leurs sens s'opposent.

Avant un GO, il faudra qualifier la conversion du registre en positions nettes
et ordres natifs. Aucune file maker, économie de netting ou fill garanti supposé.
Cette étude reste taker et préalable à une implémentation d'exécution.

## Risque et coûts

Arrêt global irréversible à **30 % de drawdown observé**, depuis le sommet,
latent/frais/funding/infra compris ; fermeture des deux mécanismes au prochain
open+60 s, dépassements conservés. Aucune relance indépendante après arrêt.
Marge cross hypothétique, maintenance stress20 % du brut non compensé ;
les limites de marge ne sont pas relâchées avec le drawdown.

Scénarios inchangés : central frais4,5/slippage2 bps par côté ; coûts9/5 ;
retard1 h ; funding adverse ; zéro coût. Infra0 et20 $/30 jours hypothétiques,
débités **une seule fois**. Données oracle/fill approchées par opens horaires.

Publier les40 simulations (4 caps, 5 scénarios, 2 infra), courbe, total net,
équivalent mensuel, contributions par mécanisme/actif, refus, marge et
drawdowns observés/enveloppe. Aucun mois rouge veto. Passage préliminaire :
quatre scénarios payants positifs, enveloppe <=30 %, marge sans rupture.
Comparer l'économie à10 % puis15–20 % mensuels, sans garantie.

Le panel est déjà consulté. Si un candidat existe, vérifier concentration,
incertitude et autres données gratuites avant promotion. Sinon conserver le
résultat sans optimiser les poids ou retirer les actifs perdants. Valider que
les branches anciennes du moteur conservent leurs résultats économiques.
Aucun nouvel appel réseau, achat, ordre, service ou serveur modifié.
