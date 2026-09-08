# Rattrapage SKHX/NVDA avant préouverture : test enregistré

Qualification des sources terminée, aucun PnL SKHX calculé. Période native
10 mars–6 septembre 2026 exclusif, 180 jours. SKHX nouvellement téléchargé,
NVDA déjà étudié ; ce n'est pas un holdout indépendant de toute la recherche.
Hypothèse unique : une divergence relative apparue pendant la fermeture externe
coréenne se corrige lors du retour des prix externes.

## Règle et causalité

Dates UTC du lundi au jeudi, session américaine ouverte et session coréenne
du lendemain ouverte d'après les fermetures XYZ 2026, complétées avant calcul
par les fermetures KRX des **3 juin et 17 juillet**, omises dans la page XYZ.
Ces dates figurent dans l'[avis Samsung Securities](https://www.samsungpop.com/ux/kor/customer/notice/notice/noticeViewContent.do?MenuSeqNo=23996)
et les [avis du service KRX](https://strn.krx.co.kr/corebbs5/BHPSTRN0401/list).
Pas de vendredi/week-end.
Retour logarithmique de chaque actif entre l'open 11:00 et le close 21:00
(connu à 22:00 UTC). Cette fenêtre commence à la fermeture externe coréenne
20:00 KST et termine avant la prochaine préouverture.

OLS du rendement SKHX sur NVDA, sur les **20 dernières dates admissibles
antérieures** ; la date signal est exclue puis ajoutée pour les jours suivants.
Exiger bêta entre 0,25 et 4, corrélation >=0,3, sigma résiduel >=0,003.
Signal si **2 <= |z| <6** et résidu absolu >=0,01 (en log-rendement).
Vendre SKHX si résidu positif, acheter si négatif ; jambe NVDA opposée,
poids 1/(1+bêta) et bêta/(1+bêta), quantités figées pendant le cycle.
Pas d'inversion, changement de seuil ou horizon après résultat.

Entrée supposée à **22:01 UTC**, prix de l'open 22:00. Sortie après **3 h**,
à 01:01 UTC. Retard : les deux transactions décalées d'une heure (23:01–02:01),
signal initial conservé. L'horaire traverse la transition externe sans présumer
de son tick exact. Un seul événement par date, aucun chevauchement entre dates.

Exclure un signal d'apprentissage si une bougie de sa fenêtre a un volume nul.
Pour l'exécution, ne pas fabriquer de prix : un volume nul sur une bougie entre
l'entrée et la sortie incluses invalide le scénario, et reste publié comme
exclusion de données ; cette vérification ex post ne constitue pas une règle
de sélection live. Un candidat positif avec exclusions devrait être requalifié.

## Coûts et décision

Moteur constant-quantity et funding timestampé existants réutilisés. Frais
natifs growth 0,9 bps et slippage 2 bps par côté sur chaque jambe. Stress :
frais 9 bps (sans growth) et slippage 5 ; retard 1 h ; funding toujours adverse ;
contrôle zéro coût. Funding valorisé avec l'open horaire, proxy de l'oracle.

Publier événements, exclusions, moyennes nettes par notional brut total,
profit factor, total sans meilleur événement, contributions mensuelles et
proxy à 1 000 $ de notional brut constant. Ce proxy n'est pas le rendement
d'un portefeuille : pas d'arrondis ni sizing/marge qualifiés ici. Sensibilité
d'infrastructure 0 /20 $ par 30 jours, aucune dépense réelle. Pas de veto sur
un mois rouge ; juger le résultat global net. Tous les scénarios payants doivent
être globalement positifs pour poursuivre la qualification économique.

Comparer descriptivement les segments avant/après le 16 juillet, sans les
présenter comme un holdout strict ni choisir après coup un segment gagnant.
Si positif, poursuivre avec contrôles, concentration, incertitude, portefeuille
continu et risque 20 % latent inclus, marge isolée et fills gratuits disponibles.
Si négatif après coûts, conserver l'échec et changer de piste. Aucun GO issu
de ce seul écran événementiel. Aucun achat, ordre ni serveur modifié.
