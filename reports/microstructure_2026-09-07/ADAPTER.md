# Précision d'adaptateur avant tout résultat économique

La documentation native précise que `tid` est un hash d'identifiants d'ordres,
et que l'identifiant global est `(block_time, coin, tid)` :
[subscriptions](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions).
La déduplication utilisera donc **coin/time/tid**, correction de la mention
coin/tid dans le protocole, sans changement de signal ni de seuil.

L'extraction initiale `pilot/2026-08-16` est conservée comme audit technique
mais ne sert pas au calcul. Les extractions `pilot_verified/` appliquent cette
clé et le warmup de 60 s après chaque frontière de fichier prévu au protocole.
Les changements de run collector provoquent aussi une remise à zéro.
Ces corrections sont enregistrées avant tout calcul de signal/markout/PnL.
