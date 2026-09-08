# Rapport or/argent : hypothèse figée avant calcul

Réutiliser les 206 jours horaires et funding natifs GOLD/SILVER déjà collectés.
Les rendements de cette période ont été vus dans un test de tendance différent :
exploration, pas réserve globalement vierge. Aucun nouvel achat ou appel API.

## Signal et sorties

Calculer log(close_GOLD / close_SILVER). Moyenne et écart-type d'échantillon des
240 observations horaires **précédentes**, excluant la bougie signal. Modèle
admissible si sigma >=0,002. À la prochaine ouverture, entrer si 2 <= |z| <4 :
short GOLD /long SILVER pour z positif, inverse pour z négatif. Une seule paire,
notionals égaux avant arrondis, donc hedge en dollars, pas neutralité garantie.
Le ratio n'a pas de valeur de conversion fixe garantissant la convergence.

Figer moyenne et sigma à l'entrée. Sortir au premier open suivant une close où
le ratio revient à z<=0,5 pour le short GOLD, z>=−0,5 pour le long GOLD (un saut
au-delà de la moyenne déclenche aussi). Stop statistique à z>=4 pour short GOLD,
z<=−4 pour long GOLD. Sortie forcée après 72 h. Minimum 24 h depuis la sortie
avant une autre entrée. Aucun fit ou seuil modifié après résultat.

## Portefeuille et risque accepté

Equity initiale 1 000 $, sizing à l'equity courante ; notionals bruts totaux
0,5x /1x /1,5x, divisés en deux jambes, scénarios fixés simultanément. Quantités
arrondies vers le bas aux décimales natives, minimum 10 $ sur chaque jambe.
Pas d'augmentation d'une position ouverte, pas de martingale.

Observer la perte totale de la paire, frais et funding compris : si <=−3 % de
l'equity à l'entrée, fermer au prochain open. Arrêt définitif du scénario si
drawdown du compte >=20 % depuis son sommet observé, également au prochain
open. Conserver les gaps/dépassements, jamais écrêter à 3 % ou 20 %. Aucun
redémarrage après arrêt, aucune modification de limites runtime/live.

## Coûts et preuves

Réutiliser le barème snapshot natif (GOLD 9 bps, SILVER 0,9 bp par côté),
slippage 2 bps/côté. Funding signé aux opens horaires pour positions déjà
détenues. Stress : frais doublés/slippage 5 bps ; funding toujours adverse ;
retard d'une heure des décisions statistiques d'entrée/sortie (les stops
de compte restent observés chaque heure). Contrôle sans coûts. Infra 0 et
20 $/30 jours, débit horaire avec effets sur sizing et arrêts.

Publier courbe horaire du capital avec positions ouvertes, cash, frais/funding,
enveloppe adverse indépendante OHLC, mois rouges/verts (premier/dernier partiels),
drawdown, récupération, rendement cumulé et composé, ainsi que les trades et
motifs de sortie. Le chemin intrahoraire et les fills ne sont pas garantis par
les bougies. Pas de déduction de liquidité à partir d'un prix affiché seul.

Les mois rouges ne sont pas un veto. Retenir pour réplication seulement les
scénarios globalement positifs en central, coûts renforcés et funding adverse,
avec drawdown horaire ET enveloppe OHLC <=20 %. Mesurer l'économie sur les
206 jours complets, sans effacer warm-up ou périodes défavorables. Cible
utilisateur 150–200 $ mensuels en moyenne acceptables ; aucun montant garanti.
Un candidat doit ensuite survivre à d'autres données et à un examen de
l'exécution et du risque avant toute promotion. Douze mois non prouvés ici.
