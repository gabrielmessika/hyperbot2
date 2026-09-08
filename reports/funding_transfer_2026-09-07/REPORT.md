# Funding 72 h : généralisation rejetée

**La piste récente à +15,3 % mensuels équivalents n'est pas un edge robuste
établi.** Le test de transfert sur 18 actifs hors CASHCAT perd **179,44 $ sur
180 jours continus**, avant coût d'infrastructure supplémentaire, et déclenche
l'arrêt de drawdown. La promotion est suspendue ; les résultats récents restent
conservés comme un épisode positif non généralisé.

## Acquisition et protocole

[Protocole enregistré](PROTOCOL.md) avant acquisition : mêmes signaux, holding
72 h, taille 0,4x, arrondis, funding, coûts et limite 20 %. CASHCAT est exclu
explicitement pour manque d'historique ancien ; il ne s'agit pas d'une longue
réplication de cet actif. L'univers reste sélectionné selon le volume courant.

**144 appels natifs gratuits, 12 423 888 octets**, deux lots séquentiels, sans
credential. Les 18 actifs ont tous 3 072 bougies et paiements horaires sur les
128 jours manquants ; aucune exclusion supplémentaire pour couverture.
Avec les archives réutilisées, les 18 actifs couvrent **180 jours complets**,
du 10 mars au 6 septembre exclusif. Aucun trou ni volume nul.

Le [tarif public](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees.md)
confirme 4,5 bps taker par côté au tarif de base courant ; stress à 9 bps,
slippage 2/5 bps, retard 1 h et funding adverse. Budget infra 0 ou 20 $/30 jours,
hypothétique et débité chaque heure. Les scénarios historiques restent des
modèles de prix open+60 s et d'oracle, pas des exécutions ni liquidations prouvées.

## Résultat principal : portefeuille continu

| Scénario funding 72 h | Net 180 j, infra 0 | Net 180 j, infra 20 $/30 j |
|---|---:|---:|
| Central | **−179,44 $** | **−250,29 $** |
| Coûts renforcés | −181,87 $ | −255,87 $ |
| Retard 1 h | −183,51 $ | −246,92 $ |
| Funding adverse | −182,14 $ | −252,06 $ |
| Sans coût de trading | −180,06 $ | −250,53 $ |

Central sans infra : **53 trades**, DD observé **20,15 %**, enveloppe OHLC
**22,68 %**, arrêt le **5 juin à 06:00 UTC**. Le compte finit à 820,56 $ ; aucun
gain ultérieur n'est crédité après son arrêt. Les frais d'infrastructure,
lorsqu'ils sont supposés, continuent après arrêt selon le protocole et portent
le drawdown à 26,20 % ; ce n'est pas une nouvelle activité de trading.

La perte subsiste sans aucun coût de trading. Le fait que le contrôle zéro coût
ne domine pas strictement chaque scénario s'explique notamment par l'absence
des crédits de funding et les trajectoires d'arrêts différentes.

## Segments et contrôles

| Fenêtre / règle centrale sans infra | Funding 72 h | Panier conservé | Panier périodique |
|---|---:|---:|---:|
| Antérieure, 128 jours | −179,44 $ | +56,81 $ | +69,68 $ |
| Récente, 52 jours, compte réinitialisé pour comparaison | +95,02 $ | +186,53 $ | +98,47 $ |
| Continue, 180 jours | −179,44 $ | +264,81 $ | +261,44 $ |

Les segments **ne s'additionnent pas** : la simulation continue conserve son
arrêt et ne redémarre pas le 16 juillet. La fenêtre récente des seuls 18 actifs
donne +5,38 % mensuels équivalents sans infra, +3,32 % environ avec infra,
bien en dessous du résultat court incluant CASHCAT. Le panier conservé rapporte
davantage avec une enveloppe de 13,70 % sur 180 jours ; ce contrôle n'est pas
promu comme nouvelle stratégie ni présenté comme alpha.

La règle funding a quatre périodes calendaires rouges et trois neutres en
central continu ; mars et septembre sont partiels. **Le motif du rejet est
le total net négatif et le risque dépassé, pas l'existence de mois rouges.**
Le temps maximal sous le sommet atteint 119,75 jours. Les pertes principales
viennent de ZEC (−61,45 $), LIT (−53,84 $), WLD et XMR (environ −22,6 $ chacun).

## Décision et suite

Statut : [FUNDING_GENERALIZATION_REJECTED_RECENT_EPISODE_UNQUALIFIED](review.json).
Le portefeuille récent CASHCAT n'est pas effacé, mais sa rentabilité ne permet
pas de conclure que le mécanisme se généralise. Pas de nouvelle réduction de
taille, suppression d'actif perdant ou changement de seuil pour sauver ce test.

Prochaine hypothèse distincte : écarts de rendement d'altcoins après couverture
par BTC, avec régression sur rendements passés et positions acheteuse/vendeuse.
Les 180 jours natifs sont désormais disponibles gratuitement ; réutiliser ce
panel et le moteur de coûts avant toute nouvelle acquisition.

**93 artefacts reproduits exactement** et résultats économiques du premier run
inchangés après formatage : [preuve](reproduction.json). Moteur source inchangé
depuis les 251 tests et mypy 64 sources ; lint/format 235 fichiers passent.
Versions du script d'acquisition et des sources archivées. Aucun achat, ordre,
service relancé ou changement serveur. Recherche globale active.
