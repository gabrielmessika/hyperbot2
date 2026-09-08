# Positions nettes : candidat conservé, traduction directe non qualifiée

Le portefeuille 50/50 cassures et rotation hebdomadaire reste une piste de
recherche à exposition 1,5x et plafond de drawdown 30 %. Cet audit ne change
aucun gain historique : il vérifie la traduction de ses positions virtuelles
en positions natives. Il révèle des petits ajustements dont l'exécution
doit être traitée avant de présenter le portefeuille comme exécutable.

## Périmètre et méthode

18 actifs, 204 jours du 14 février au 6 septembre 2026 exclu, 4 896 heures.
Caps 1,5 et 2x, cinq scénarios, infrastructure marginale nulle ou sensibilité
hypothétique 20 $/30 jours : vingt cas enregistrés avant calcul. Sources
gratuites déjà présentes ; aucun nouvel appel de marché ni achat.

Signaux, quantités et dates acceptées sont figés. La somme signée par actif
donne le changement de position native. Le cash et l'equity sont reconstruits
heure par heure avec tous les frais, slippages, fundings et coûts originaux ;
ils coïncident avec les sources à 1e-18 $ près. Aucune économie d'exécution
n'est créditée. Ce contrôle ne constitue pas un nouveau replay d'ordres.

Le minimum documenté est de 10 $ par ordre. La page consultée ne démontre
pas d'exception générale pour les réductions ; elles restent donc soumises
au contrôle conservateur. [Erreurs API Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/error-responses).

## Résultats

| Scénario sans infrastructure | Net historique inchangé | Enveloppe brute originale | Enveloppe nette auditée | Ajustements <10 $ |
|---|---:|---:|---:|---:|
| 1,5x central | +538,72 $ | 27,17 % | 27,12 % | 18 |
| 1,5x coûts renforcés | +236,54 $ | 29,41 % | 29,36 % | 25 |
| 1,5x entrée retardée | +378,88 $ | 28,67 % | 28,67 % | 17 |
| 1,5x funding adverse | +381,00 $ | 28,45 % | 28,41 % | 20 |
| 2x central | +698,48 $ | 34,63 % | 34,57 % | 15 |

À 1,5x central : 2 130 jambes virtuelles deviennent 2 049 deltas nets non
nuls. Sur les 18 ajustements trop petits, onze ouvrent/augmentent une position
et sept la réduisent. Exemples : augmentation short FARTCOIN de 3,65 $,
augmentation short ZEC de 4,27 $, réduction LIT de 8,69 $. Les tailles
respectent toutes les décimales natives ; c'est le montant minimum qui pose
problème. Même une éventuelle exception reduce-only ne réglerait pas tout.

Le notionnel échangé théorique passe de 342 619,19 $ à 330 278,24 $, sans
créditer l'économie correspondante. Pendant 2 352 heures sur 4 896, au moins
un actif porte des positions virtuelles opposées. Leur compensation ne
réduit pourtant que peu le pire drawdown conservateur de ce portefeuille.
Le ratio brut net maximal aux clôtures horaires vaut 1,672x : le cap 1,5x
porte sur l'allocation à l'entrée, il n'est pas un plafond continu garanti.

Les vingt cas contiennent des petits ordres (11 à 25 chacun), aucun mauvais
lot. À 2x les scénarios payants sans infrastructure restent au-dessus de
30 % d'enveloppe nette (34,57–36,98 %). Avec la sensibilité hypothétique de
20 $, le scénario 1,5x retard repasse sous 30 % après compensation (29,70 %),
mais le stress de coûts reste au-dessus (30,38 %). Aucun nouveau GO.

## Limites et suite

L'enveloppe OHLC nette conserve les coûts originaux et combine prudemment les
expositions aux frontières de chaque heure. Ce n'est ni un chemin intrahoraire
observé, ni une validation des fills, ticks de prix, prix oracle ou marges
réels. Le respect du seul minimum ne suffirait pas à qualifier l'exécution.

La prochaine étape est un simulateur causal de positions natives : conserver
en inventaire les petits écarts non exécutés, recalculer les ordres suivants,
le funding, les coûts et le risque sur les positions effectivement détenues.
Ne jamais ignorer un ordre tout en créditant gratuitement sa position cible.
Garder 1,5x, les mêmes signaux et les poids 50/50 ; aucune optimisation motivée
par ces résultats. Ensuite, validation gratuite indépendante nécessaire.

Statut : **FIXED_NATIVE_DELTAS_REQUIRE_EXECUTION_PLANNER**. Le résultat
central antérieur de 6,54 % équivalents mensuels reste exploratoire ; ni
espérance future positive ni cible nette de 10 % ne sont démontrées.

## Reproduction

`scripts/investigate_netting.py` produit vingt audits, une qualité et un
résumé ; chaque source et artefact possède son SHA-256. Deux exécutions
hors réseau sont comparées dans `reproduction.json`. Huit nouveaux tests
couvrent compensation, expositions restantes, petits deltas, coûts/funding
conservés et corruption des entrées. Suite complète : 275 tests passent ;
lint, format et mypy sont vérifiés. Aucun ordre, service ou serveur modifié.
