# Condition de tendance collective, chronologie continue

Hypothèse nouvelle après l'échec du panier constamment acheteur : n'engager
le panier hebdomadaire que lorsque la tendance collective passée est positive.
Pas de modification selon les pertes d'un actif ou d'une date particulière.

Condition unique fixée : médiane des onze rendements arithmétiques sur30 jours,
close[i-1]/close[i-721]-1, strictement supérieure à zéro. Les prix sont tous
antérieurs à l'entrée. Chaque lundi00h UTC, si la condition est satisfaite,
acheter les trois volatilités30 jours les plus faibles et les trois plus
fortes, aux mêmes poids notionnels égaux et avec la garde168h déjà définie.
Sinon aucune nouvelle position cette semaine. Aucun changement de condition
en cours de semaine ; les positions précédentes expirent selon leur horizon.

Contrôle : le même panier six actifs sans condition de tendance. Deux panneaux :
Binance2024–2025 contigu (731 jours, correction REST2024 explicite conservée)
et Hyperliquid2026 (204 jours). Même univers11. Une seule initialisation de
capital1 000 $ et du warmup par panneau ; aucune remise à zéro au1 janvier2025.
Les sources2025 sont chargées/validées dans leur cohorte15 puis restreintes
aux onze actifs prédéfinis. Conserver la continuité des paiements et prix.

Recalculer les sélections. Le panneau natif doit retrouver les anciennes
sélections avant condition. Le panneau continu doit garder les semaines de
janvier2025 devenues couvertes ; publier condition et panier de toutes les
semaines, y compris les semaines en cash, sans sélectionner la meilleure année.

Diagnostic natif fixe :2 panneaux×2 règles×2 caps0,5/1,5x×2 arrêts20/30 %×
5 scénarios×2 infrastructures0/20 $ par30 jours =160 simulations. Réutiliser
le moteur sans modification. Frais/slippage4,5/2bps, stress9/5, retard1h,
funding adverse, zéro coût ; lots/ticks/minimum10 $, écarts reportés et equity
native. Infra20 est hypothétique et continue après arrêt. Caps fixés avant PnL.

Arrêt global irréversible sur drawdown observé incluant les pertes ouvertes
et coûts ; conserver dépassements et enveloppe prudente OHLC. Pas de reprise
annuelle, de clipping, martingale ou rattrapage par levier. La reprise d'une
condition de marché positive peut permettre une entrée uniquement si le
compte n'a pas déclenché son arrêt global. Aucun cap augmenté après perte.

Publier gains, équivalent mensuel sur toute la période (cash/warmup/arrêt inclus),
mois et années du même compte continu, drawdowns, arrêts, marge et positions
terminales. Les deux périodes ne sont pas chaînées entre plateformes.
Compatibilité historique : pour chaque cap/limite/infra, tous les scénarios
payants des deux panneaux doivent être positifs, enveloppe sous la limite,
marge sans incident et bilan terminal plat. Comparer le contrôle sans condition.

Toute configuration compatible serait au plus un candidat de recherche ;
les périodes déjà consultées, le choix de cette hypothèse après d'autres
essais, le transfert de plateforme et les fills proxy interdisent un GO
automatique ou une garantie de gain. Conserver l'échec des règles précédentes.
Pas de balayage de fenêtres, seuils ou fréquence après PnL. Aucun achat ni
nouvel appel de marché nécessaire. Si les rendements ou le risque échouent,
archiver avant de choisir une autre hypothèse.
