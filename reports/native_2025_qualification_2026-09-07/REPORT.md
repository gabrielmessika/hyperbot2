# Sonde bornée : historique Hyperliquid 2025 disponible sur ARB

**Complément terminé : la cohorte complète de onze actifs échoue à la
qualification 2025.** La disponibilité d'ARB ne s'étend pas à XMR et ZEC.
Voir le contrôle ci-dessous ; aucune collecte annuelle de funding engagée.

**Information nouvelle sur les données, aucun edge validé.** Deux requêtes
publiques, 312 275 octets, aucun achat et aucun backtest. ARB est choisi comme
premier actif par ordre alphabétique de l'univers existant, pas selon son PnL.

- Bougies ARB 4 h : 2 190 lignes couvrant toute l'année 2025, sans trou,
  doublon ni volume nul ; horodatages, durée et cohérence OHLCV vérifiés.
- Funding ARB : les 48 règlements horaires demandés du 1er au 3 janvier 2025
  exclu sont présents, avec offsets de 38 à 54 ms aux bornes de l'échantillon.
  L'année complète de funding n'a pas été demandée ni qualifiée.

[Enregistrement avant requêtes](registration.json),
[résultat contrôlé](qualification.json). Réponses brutes, SHA-256 et manifeste
dans `data/native_2025_qualification_2026-09-07/`. Client public existant réutilisé.

La [documentation officielle](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)
annonce les 5 000 dernières bougies et accepte l'intervalle 4 h. La réponse
observée confirme ici la couverture 2025 pour ARB. Elle ne prouve ni la
couverture des dix autres actifs, ni celle des bougies horaires anciennes,
ni des carnets, prix oracle ou fills réels. Ne pas interpoler les bougies 4 h
pour prétendre reconstituer l'exécution horaire des études précédentes.

Cette source pourrait lever une limite matérielle des transferts Binance
pour un test lent préexistant. Avant tout PnL éventuel : qualifier le même
univers complet, garder les règles figées et traiter explicitement le changement
de résolution et les stress d'exécution. Aucun résultat de transfert antérieur
n'est effacé, aucun candidat nouveau n'est sélectionné sur ces données.

La sonde est terminée à son plafond de deux appels. Le test de choc collectif
reste suspendu. Aucun service, serveur ou trading réel modifié ; objectif
économique non atteint.

## Extension bornée aux dix autres actifs

[Enregistrement](cohort_registration.json),
[qualité de la cohorte](cohort_qualification.json). Dix requêtes supplémentaires,
2 651 374 octets ; total avec la sonde ARB : douze appels et 2 963 649 octets.
Le client existant est inchangé, les réponses et checksums sont conservés.

Neuf actifs ont chacun les 2 190 bougies 4 h attendues, sans trou ni volume
nul : ARB, BNB, DOGE, INJ, LINK, NEAR, UNI, WLD et XRP. Les deux autres échouent :

| Actif | Bougies reçues | Bougies manquantes | Bougies reçues à volume nul |
|---|---:|---:|---:|
| XMR | 912 | 1 278 | 912 |
| ZEC | 1 542 | 648 | 999 |

Ces réponses ne qualifient pas les prix et fills historiques nécessaires.
Elles ne permettent pas, à elles seules, d'attribuer les trous à une date
précise de listing ou de prouver l'impossibilité de tout ordre à volume nul.
Les garde-fous de données restent appliqués, sans interpolation ni remplissage.

## Conséquence pour le candidat acheteur antérieur

Les sélections des 47 paniers de l'étude acheteuse Binance 2025 sont relues
sans modifier leurs actifs ni calculer de nouveau PnL. Pour chaque actif
sélectionné, vérifier les bougies natives 4 h de l'entrée à la sortie à 168 h,
sortie incluse. **38 paniers sur 47 échouent déjà à cette couverture minimale** :
XMR affecte les 38, ZEC en affecte seize inclus dans ces 38.
[Contrôle détaillé](prior_basket_coverage.json).

Les neuf autres paniers ne sont pas pour autant validés : ce contrôle ne
qualifie ni les trente jours de chauffe, ni le funding annuel, ni les fills.
Il interdit surtout de présenter les anciens gains Binance comme des gains
reproductibles à l'identique sur Hyperliquid 2025. Cette limite était signalée
comme transfert de plateforme ; son incidence est maintenant mesurée.

Décision : arrêter cette qualification à son plafond, sans télécharger le
funding annuel d'une cohorte déjà rejetée. Ne pas supprimer XMR/ZEC puis
présenter le nouveau panier comme une validation du précédent. Un univers
fondé sur la disponibilité historique constituerait une autre expérience,
à justifier séparément ; aucune n'est lancée ici. Pas de nouvelle stratégie,
de backtest, de dépense ou de modification serveur. Aucun GO économique.
