# Rattrapage SKHX/NVDA : hypothèse non confirmée

**Quatre signaux sur 180 jours**, gain central trop petit et perdu sous stress.
Le test de rattrapage relatif avant préouverture ne fournit pas un edge
économiquement intéressant. Aucun GO, aucune simulation de portefeuille promue.

## Règle et données

Régression des rendements SKHX/NVDA pendant la fermeture externe coréenne,
11:00–22:00 UTC, sur vingt dates admissibles strictement antérieures. Signal
à |z| entre 2 et 6 et résidu absolu au moins 1 %, avec filtres de bêta,
corrélation et volatilité. Correction du résidu avec couverture NVDA à bêta
figé, entrée 22:01 et sortie 01:01 supposées aux opens horaires.

Dix appels gratuits ont fourni les 4 320 heures SKHX et le funding ; NVDA
réutilisé localement. Voir [qualification](QUALIFICATION.md) et `PROTOCOL.md`.
82 dates exclues par calendrier, vingt par chauffe/modèle dégénéré, 74 par
modèle ou seuil, quatre retenues. Aucune exclusion de volume nul sur les
fenêtres de signal admissibles ou sur ces quatre exécutions ; les 24 bougies
SKHX sans volume restent documentées dans le dataset, sans interpolation.

Les fermetures des 3 juin et 17 juillet ont été ajoutées **avant calcul** au
calendrier XYZ incomplet : [avis Samsung Securities pour le 3 juin](https://www.samsungpop.com/ux/kor/customer/notice/notice/noticeViewContent.do?MenuSeqNo=23996)
et [avis du service KRX pour les deux dates](https://strn.krx.co.kr/corebbs5/BHPSTRN0401/list).
Sources archivées, pas de sélection de jours après lecture du PnL.

## Résultats économiques

Les dollars ci-dessous sont un **proxy avec 1 000 $ de notional brut constant
partagé entre les deux jambes**, pas le rendement d'un compte : sizing,
arrondis, marge et drawdown latent non qualifiés dans cet écran préalable.

| Scénario | Moyenne nette par événement | Proxy cumulé, 180 jours |
|---|---:|---:|
| Central | +21,58 bps | +8,63 $ |
| Coûts renforcés | −1,04 bps | −0,42 $ |
| Retard 1 h | −6,59 bps | −2,64 $ |
| Funding adverse | +15,48 bps | +6,19 $ |
| Sans coût de trading ni funding | +24,99 bps | +10,00 $ |

Frais centraux 0,9 bps et slippage 2 bps par côté ; stress 9/5. Funding natif
pendant la détention, oracle valorisé par proxy horaire. Le net central revient
à **1,44 $ par 30 jours** avant infrastructure ; une sensibilité hypothétique
de 20 $/30 jours le ramène à −18,56 $. Aucune dépense engagée.

PF central 1,22 ; en retirant le meilleur événement par simple soustraction
comptable, le total devient −37,99 $. Pire événement −33,98 $.

| Date du signal UTC | Sens SKHX | Proxy net central |
|---|---|---:|
| 27 avril | Achat | +1,77 $ |
| 5 mai | Vente | −5,78 $ |
| 7 mai | Achat | +46,62 $ |
| 30 juillet | Vente | −33,98 $ |

Le segment antérieur au 16 juillet vaut +42,61 $ sur trois événements, le
segment récent −33,98 $ sur un seul. Il ne s'agit pas d'un holdout statistique.
Le rejet porte sur le gain global minime, sa concentration et sa disparition
sous stress ; un mois rouge n'est pas un veto. Quatre observations ne permettent
pas une estimation fiable de fréquence mensuelle ou de robustesse annuelle.

## Décision et validation

`HYPOTHESIS_NOT_CONFIRMED`. Ne pas sauver le test en inversant les positions,
en retenant seulement mai ou en modifiant les seuils après résultat. La nouvelle
base gratuite SKHX reste réutilisable pour une hypothèse distincte.

Les 20 % de drawdown utilisateur ne sont **pas validés** par ce proxy ; aucun
intérêt économique établi ne justifie ici la qualification complète de marge
isolée et d'exécution. Les documents courants ne prouvent pas les horaires et
frais historiques à la minute ; ce test horaire était volontairement préalable.

Quatre artefacts du test et un artefact de qualification reproduits exactement.
257 tests passent ; lint/format251 fichiers et mypy66 sources passent.
Code de pricing, funding, OLS et client public réutilisé ; aucune dépendance
runtime vers un ancien bot. Aucun ordre, achat, secret, service ou serveur
modifié. Recherche active ; conserver les échecs et changer de mécanisme.
