# Tolérance aux pertes dans la recherche

Décision utilisateur du 7 septembre : accepter des sessions et mois rouges,
par exemple huit mois gagnants sur douze, tant que l'ensemble reste largement
positif. L'objectif +15 % ou +20 % mensuels acceptable ne doit pas être lu
comme une exigence de gain chaque mois.

Question ultérieure de l'utilisateur : une cible abaissée à **+10 % nets par
mois** rendrait-elle les stratégies déjà étudiées intéressantes ? Ajouter cette
sensibilité économique (100 $ pour 1 000 $) aux comparaisons. Elle ne valide
pas rétroactivement un candidat fragile, ne change pas le drawdown accepté et
ne devient pas une promesse de gain chaque mois.

## Évaluation à appliquer aux prochains tests

**Mise à jour ultérieure :** l'utilisateur accepte davantage de risque et
demande l'effet d'un drawdown à **30 %** si l'espérance de gains est supérieure.
Les simulations peuvent donc utiliser 30 %, en conservant 20 % comme comparaison.
Les mentions 20 % ci-dessous décrivent la décision initiale. Ne pas modifier les
anciens résultats ; publier les dépassements réels et conserver latent, coûts,
marge et absence de reprise après arrêt. Aucun changement de limites live.

- Privilégier le résultat cumulé **net** et sa distribution sur des périodes
  suffisamment longues ; publier rendement arithmétique et composé sans les
  confondre. Ne pas extrapoler une courte série à douze mois validés.
- Publier mois gagnants/perdants, gain moyen des mois verts et perte moyenne
  des mois rouges, pire mois, drawdown mesuré sur la courbe complète disponible,
  durée sous le précédent sommet et durée de récupération. Un drawdown aux
  seules sorties de positions ne suffit pas à décrire le risque intraday.
- Ne pas rejeter une règle parce qu'un mois ou une fenêtre chronologique est
  rouge. Examiner si les pertes sont supportables, si le résultat global
  compense le risque et si l'avantage subsiste ailleurs. L'absence de profit
  dans chaque fenêtre ne constitue plus, à elle seule, un veto de recherche.
- Plafond choisi explicitement par l'utilisateur : **20 % de drawdown depuis
  le sommet du capital**, soit 200 $ lorsque ce sommet vaut 1 000 $. Calculer
  `drawdown(t) = 1 - equity(t) / max(equity(u), u <= t)`, positions ouvertes et
  coûts inclus. Une stratégie dépassant ce plafond dans le scénario évalué
  ne satisfait pas cette tolérance. Les sensibilités plus prudentes restent
  possibles ; 30 % n'était pas accepté à cette étape initiale (voir mise à jour
  ultérieure ci-dessus). Une mesure aux seules sorties
  ne valide pas le risque intraday, et un seuil de simulation ne garantit pas
  un prix de sortie réel en cas de gap ou de manque de liquidité.
- Toute hausse de taille doit être appliquée aussi aux pertes, frais, funding,
  marge et stress d'exécution. Ne pas multiplier uniquement le gain moyen ou
  augmenter la taille après une perte. Aucune martingale.
- Séparer le PnL net de trading et l'hypothèse de coût d'infrastructure ; conserver
  les sensibilités à coût supplémentaire nul et à 20 $/mois. Le coût marginal
  réel n'est pas attesté par l'hypothèse de 20 $ utilisée dans les premiers tests.

Huit mois positifs ne sont pas une preuve en soi. Exemple purement arithmétique,
sans composition : huit gains de 50 $ et quatre pertes de 150 $ donnent −200 $.
Huit gains de 100 $ et quatre pertes de 50 $ donnent +600 $. Il faut tester les
montants et l'ordre des pertes, pas seulement leur fréquence.

## Ce que cette décision change dans le suivi

Les protocoles et résultats antérieurs restent conservés. Les nouveaux tests
utilisent cette tolérance ; toute réévaluation d'une ancienne règle doit être
étiquetée comme telle, sans effacer les échecs ni présenter les données déjà
consultées comme hors échantillon. Les exigences de causalité, coûts réalistes,
réplication et absence de biais de sélection subsistent.

La règle COIN/MSTR/BTC calculée aujourd'hui reste négative **sur l'ensemble des
180 jours** dans les deux directions après coûts. L'accepter avec des mois
rouges ne modifie donc pas son diagnostic. En revanche, une règle globalement
positive ne doit plus être écartée uniquement à cause de mois déficitaires.

Cette autorisation concerne les simulations et la comparaison des risques.
Aucune configuration de trading, limite du superviseur en production ou
autorisation d'ordre réel n'est changée. Aucun achat de données.
