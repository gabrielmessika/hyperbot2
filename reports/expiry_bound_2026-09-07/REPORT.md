# Fin d'échéance : borne optimiste et qualité des références

**Aucun edge validé.** La borne ne suffit pas à rejeter toute stratégie en fin
d'échéance, mais ne constitue pas un candidat rentable. Les références legacy
exigent une correction de causalité avant tout backtest. Recherche gratuite,
offline, sans ordre ni changement serveur.

## Périmètre et calcul

Le [protocole](PROTOCOL.md) a été enregistré avant les résultats. Réutilisation
de 892 492 lignes Nautilus et des résolutions natives de 115 contrats : 40 dates
d'expiration entre le 28 mai et le 7 juillet 2026, enveloppe de 41 jours.
Les deux sondes exclues du précédent test causal sont incluses ici : connaître
le gagnant futur est précisément l'hypothèse volontaire de cette borne.

Capital total de 1 000 $ partagé par échéance, sans composition. Achat du seul
côté gagnant connu a posteriori, puis paiement final ; aucune erreur de signal.
Unités fractionnaires, aucun minimum d'ordre, fills immédiats sans concurrence.
Les scénarios à 7 bps supposent seulement une retenue sur le paiement final,
sans frais d'ouverture : ce sont des hypothèses optimistes, pas un relevé de
commissions historiques. Les 20 $ d'infrastructure mensuels sont une hypothèse
de calcul, aucune dépense engagée.

| Borne avec retenue de 7 bps | Gain idéal sur 41 jours | Équivalent /30 jours après 20 $ |
|---|---:|---:|
| Prix à cinq minutes, toute la taille au meilleur ask | 2 183,01 $ | 1 577,33 $ |
| Prix à cinq minutes, 10 % de cette taille | 276,05 $ | 181,99 $ |
| Meilleur prix des six dernières minutes, profondeur infinie | 7 553,03 $ | 5 506,61 $ |

**Aucune ligne n'est un rendement réalisable du bot.** La dernière connaît
aussi le meilleur instant futur et suppose une liquidité infinie. Ces bornes
ne portent que sur les prix observés, pas sur les périodes sans observations.
La limite de 10 % est une sensibilité de capacité, pas une preuve de fill.

## Pourquoi 181,99 $ ne valide pas l'objectif de 150–200 $

Un seul contrat, `SOL_GT_80.457_20260706_0600`, produit 173,29 $ du gain idéal,
soit **62,77 %**. Le scénario achète son côté NO à 0,433 grâce à la connaissance
du résultat futur. Ce prix n'a rien d'un paiement presque certain déjà connu
au moment de l'achat. Retirer cette seule allocation réduit l'équivalent à
**55,19 $/30 jours**, toujours avec connaissance de tous les autres gagnants.
Cette suppression est un diagnostic de concentration, pas une sélection de
stratégie enregistrée avant test.

À l'instant fixe, seuls 25 contrats ont un ask gagnant utilisable ; 82 ont un
ask vide/invalide et huit n'ont pas d'observation récente. Dans les six dernières
minutes, 1 445 des 1 851 observations du côté gagnant n'ont pas d'ask utilisable ;
26 contrats seulement en ont au moins un. Une borne élevée sur des observations
rares ne démontre ni fréquence exploitable ni capacité quotidienne.

## Audit de causalité des références

Les fichiers `short_expiry_features.csv` mainnet et paper comprennent
respectivement 1 563 et 1 490 lignes, sur 110 marchés /41 dates largement
communs. Ils ne constituent pas deux échantillons indépendants.

Le champ `seconds_left` utilise le début de boucle, tandis que `ts` est écrit
après les acquisitions séquentielles. L'écart médian est **22,824 s** mainnet et
**23,029 s** paper, avec un maximum proche de 28 s. Dix lignes mainnet et treize
paper sont enregistrées à l'échéance ou après celle-ci. Reconstituer l'instant
de disponibilité par `expiry - seconds_left` introduirait une anticipation.
Utiliser au plus tôt l'horodatage de journalisation ; celui-ci ne garantit pas
à lui seul la fraîcheur de chaque composant de la référence.

Le fichier mainnet `decisions.jsonl` fournit une référence journalisée dans la
minute précédant la décision à cinq minutes pour **42 des 115 contrats** :

- OKX : horodatage source âgé de 0–60 s pour les 42 références.
- Coinbase : 41 références dans cette plage, une hors plage.
- Hyperliquid, Bybit et Kraken : aucun horodatage exchange dans ces 42 entrées.
- Binance : 31 entrées, aucune avec un horodatage exchange.

Ces logs sont conditionnés par les opportunités détectées par l'ancien bot :
les références manquantes ne forment pas un échantillon aléatoire. Les prix
externes horodatés ne prouvent pas le prix natif de résolution. Aucune probabilité
ni direction legacy n'a été utilisée pour fabriquer un signal dans ce diagnostic.

## Livraison et décision

État : `BOUND_CANNOT_REJECT_REAL_SIGNAL_UNPROVEN`. Aucun GO ; aucune stratégie
à +15 %, +20 % ou +30 % démontrée. Cette étape fournit un filtre économique et
une correction nécessaire de l'usage des archives, pas une validation hors
échantillon. Les résultats et résolutions sont désormais connus : toute règle
construite dessus devra être qualifiée d'exploratoire et répliquée ailleurs.

Les sources, lignes sélectionnées et versions de code sont checksumées dans
`data/expiry_bound_2026-09-07/final/` et `reference_audit_final/`. Les premiers
essais restent conservés ; `run1` a échoué sur un ask vide avant publication,
le parseur gère maintenant les valeurs absentes et non finies. Les artefacts
finaux sont reproduits dans des répertoires distincts, voir
[preuve de reproduction](reproduction.json). 230 tests passent, ainsi que lint,
format (186 fichiers) et mypy (57 sources).

Suite de recherche : qualifier d'abord si les seules références effectivement
disponibles avant décision peuvent soutenir un test causal, avec une marge
explicite d'incertitude sur la référence native. Si cette qualification échoue,
suspendre cette voie et utiliser les autres archives gratuites ; ne pas acheter
un flux pour tenter de sauver cette borne. Aucun développement de trading fondé
sur les 181,99 $ affichés ici.
