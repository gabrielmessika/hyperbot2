# Dernier diagnostic maker — protocole avant capture

Deux témoins successifs de 60 secondes sur les outcomes BTC 1896 puis ETH
1897, sélectionnés par métadonnées le 7 septembre avant lecture des témoins.
Chaque témoin abonne simultanément YES/NO au L4 0xArchive et au L2 natif fast
Hyperliquid, depuis le même processus sur le serveur. Quatre abonnements par
témoin, aucun ordre, aucune reconnexion, aucun téléchargement massif.
Limites : 120 s par témoin autorisés par le programme, 20 Mo de messages par
flux, conteneur 256 Mo / 1 CPU, stockage des messages et horloges de réception.

Mesurer les âges à réception des deux sources et les intervalles temporels
de fraîcheur du L2. Seuils inchangés : stale 500 ms, placement hypothétique
350 ms, incertitude 50 ms, TTL 1 000 ms, annulation hypothétique 350 ms.
Une analyse de sensibilité sans placement ne changera pas les gates.

Reconstruire les diffs WebSocket dans l’ordre serveur documenté. Tout indice
local ajouté pour réutiliser le reconstructeur est strictement interne :
il ne devient jamais une séquence exchange ou une preuve de continuité.
Pour fermer un bloc de chaque côté, attendre un bloc supérieur sur ce côté ;
pour une profondeur duale, utiliser le plus petit avancement des deux côtés.
Le dernier bloc sans successeur reste censuré. Contrôler les prix/tailles/n
contre le L2 natif uniquement sur ces états ; une comparaison après réception
ultérieure peut expliquer un retard, jamais autoriser rétrospectivement un trade.

Arrêter la qualification sur gap explicite, divergence d’identité, snapshot
tronqué, bloc régressif ou erreur. Conserver les résultats partiels et leurs
limites. Un saut de numéro de bloc d’un marché calme n’est pas automatiquement
un gap. L’absence de champ seq n’est pas, à elle seule, une preuve d’omission.

Conclusion attendue : soit une voie technique documentée à poursuivre vers
la qualification maker, soit clôture NO-GO de ce candidat avec ce transport.
Aucun GO économique possible à partir de ces témoins, même favorables : frais,
référence causale, priorité duale, fills et gates A/OOS/shadow restent requis.
