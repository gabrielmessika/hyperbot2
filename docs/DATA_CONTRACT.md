# Contrats d’entrée HyperBot2

## Fenêtres de replay version 1

`scripts/make_demo.py` fournit un exemple exécutable complet. Chaque ligne JSON
est une `OutcomeWindow` sérialisée par `window_payload` ; `window_from_payload`
refuse les versions/champs inconnus et les faux booléens. Les décimales sont
encodées en chaînes, les horloges en millisecondes entières UTC.

| Champ | Contrat |
|---|---|
| `schema_version` | `1` |
| `now_ms` | Instant de décision ; ordre global de réception croissant |
| `definition` | `outcome_id`, sous-jacent, strike, expiry, instant d’observation, tick/lot, frais effectifs, règle de settlement, hash de preuve, statut |
| `book` | Carnet YES canonique à décision, horloges exchange/réception, séquence, bids/asks, tier A/B/C et qualifications |
| `fair` | Probabilité, instant de disponibilité, timestamp de référence, fin de calibration, incertitude/adverse selection en prix par token, hash source ; `null` bloque |
| `future_books` | Observations après décision jusqu’à TTL + latence d’annulation ; utilisées uniquement pour exécution/risque postérieurs |
| `trades` | Identifiant stable du match économique, côté YES/NO, horloges, séquence, côté agressif, prix et quantité |
| `healthy` | État causal du flux à la décision |
| `exposure_healthy` | Intégrité pendant l’exposition ; faux sur gap ou queue de capture incomplète, ce qui invalide le résultat économique |

Un fichier voisin `windows.jsonl.sha256` doit contenir son SHA-256. Il identifie
l’entrée entière ; ses preuves de qualité doivent être conservées séparément.
`queue_qualified` et `dual_priority_qualified` ne doivent être vrais que si un
audit indépendant de l’export les justifie. Le collector public les laisse
faux. Des drapeaux dans un JSON ne constituent pas une qualification scientifique.

Les fenêtres sont globalement non chevauchantes lorsqu’une quote est émise.
Les frames reçues avant la fin de cette exposition sont comptées `window_busy`.
Leur omission n’est donc pas confondue avec une absence de données. Le carnet
doit couvrir chaque prix coté sur toute l’exposition, avec fraîcheur ≤ 500 ms.
Les trous postérieurs invalident le run entier. Toute la liquidité visible est
placée devant l’ordre, sans avantage supposé de priorité du côté dual.

Les flux bruts du témoin se trouvent dans `raw/outcomes-fast-public.jsonl`,
au format `JsonlEventStore` HyperBot, et leurs contrôles dans le flux voisin.
La commande `prepare` et le service `run` les assemblent désormais automatiquement
en fenêtres. La qualification des références de settlement/calibrations et de
la file reste à fournir avec des preuves réelles. `CausalFairValueModel` est une brique de calcul testée,
pas une calibration rentable préentraînée ni un connecteur de référence qualifié.

## Attestations du catalogue

Exemple de structure uniquement ; les valeurs et hashes suivants sont fictifs :

```json
{
  "1715": {
    "observed_ms": 1788710908498,
    "valid_until_ms": 1788760800000,
    "active": true,
    "tick": "0.00001",
    "size_increment": "0.1",
    "settlement_rule": "mark_gt_strike",
    "specification_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "fees": {
      "maker_close_rate": "0.001",
      "taker_close_rate": "0.002",
      "settlement_rate": "0.003",
      "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  }
}
```

Les taux sont les taux **finaux effectifs**, après les règles applicables au
marché et au compte ; `feeScale` et `deployerFeeScale` seuls ne suffisent pas.
Le modèle facture `quantité × prix × taux` lors d’une fermeture et
`quantité × payout × taux` au settlement ; une ouverture est à frais nuls selon
la thèse du plan. Aucune inférence de tier utilisateur ni rétroactivité.
Toute opération non couverte par ce modèle exige une extension testée avant usage.

La règle `mark_gt_strike` doit être attestée pour le contrat concerné ; le parser
ne la déduit pas d’un simple nom. Pas de fallback vers un prix spot/perp voisin.
Les dates d’attestation encadrent strictement la décision et les frais le fill.
