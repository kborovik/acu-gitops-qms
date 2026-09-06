# CanNordic BioNutra Inc. (`acu-gitops-qms`)

Virgin-tenant Acumatica seed for **CanNordic BioNutra Inc.** (AcctCD `CNBN`), a
Canadian CDMO and ingredient importer (NHPs, functional foods). Finance +
inventory/distribution + kit assembly. QMS tenant for
[`gcp-acu-coa`](https://github.com/kborovik/gcp-acu-coa). Single full seed — no `--flavor`.

Sourced from the company profile and master data in
[`gcp-acu-coa`](https://github.com/kborovik/gcp-acu-coa/blob/main/domain/COMPANY_PROFILE.md).
Inventory and vendor IDs are the domain catalog IDs (length at most 30). Warehouse
`SiteCD` stays 10 characters (`WH-MISS-01`).

`config/bootstrap/segmented-key.yaml` raises CS202000 `INVENTORY` and
`BIZACCT` segment 1 to length 30 (DAC max) before StockItem / Vendor /
Customer. `ACCOUNT` and `INSITE` stay 10.

**Start from a brand-new empty tenant.** Do not apply onto a half-configured company.

Republish AcuBootstrap (`acu bootstrap`, contract 1.7.0) so Company maps CS101500 `DecPlQty` (this seed sets 3 for milligram-scale KG kit BOMs) and SegmentedKey maps `Length` to CS202000 `Detail`.

## Rebuild order

```sh
# 1. Credentials in .env (ACU_PASSWORD, ACU_TENANT, …)
#    Default API pin + REST where = committed matrix.yaml cell
#    (default_api + base_url; not sticky ACU_BASE_URL / ACU_API_VERSION)
acu config check

# 2. Publish Bootstrap (features + contract from config/bootstrap/)
acu bootstrap

# 3. Seed config umbrella (bootstrap → baseline → setup → master)
acu apply

# 4. Lifecycle scenarios (once capital → buy → build → sell)
acu run

# 5. Prove no drift
acu diff

# 6. Capture derived-state observations (EndingBalance trial-balance)
acu state
# warm gate: once-capital only — additive buy/sell moves numeric observations
acu run scenario/10-seed-capital.yaml && acu state --assert-unchanged

# 7. Cold matrix lifecycle (SSH + tenant; optional multi-cell --all)
# acu check --yes

# Optional: re-seed from live (inverse of apply; always under config/)
# acu extract --out . --force
```

Bare `acu apply` / `acu diff` also prefer `config/` when those trees exist.
`acu extract` hard-cuts emit to `config/{bootstrap,baseline,setup,master}/` (never root SEED_DIRS).

## Company

| | |
| --- | --- |
| Legal name | CanNordic BioNutra Inc. / BioNutra CanNordique |
| AcctCD | `CNBN` |
| Base currency | CAD |
| Country | CA |
| HQ | 2450 Meadowpine Blvd, Mississauga, ON L5N 6S2 |
| Site licence | Health Canada #302194 (Mfg / Pack / Label / Import) |

Warehouse: `WH-MISS-01` / `MAIN`. Buy / build / sell run there.

Item class IDs stay `PARTS` / `KITS` so `acu extract` filter-split still matches.

Kit specs follow the domain BOMs (mg/capsule × 60, as KG per bottle):
ImmunoShield `0.012` + `0.009` + `0.006` KG; CardioPure `0.060` + `0.006` + `0.001` KG.

## Catalog in this seed

| ID | Kind |
| --- | --- |
| `VEND-NORTH-BIO` | vendor |
| `VEND-ALPINE-EXT` | vendor |
| `VEND-NIPPON-PHARMA` | vendor |
| `VEND-NORDIC-MAR` | vendor |
| `RAW-ECH-EXT4` | raw |
| `RAW-ELD-EXT10` | raw |
| `RAW-ASH-EXT5` | raw |
| `RAW-COQ10-99` | raw |
| `RAW-OMEGA3-70` | raw |
| `RAW-ASTA-10` | raw |
| `FG-IMMUNE-DEFENSE-60C` | kit |
| `FG-CARDIO-OMEGA-COQ10-60SG` | kit |
| `VITALPLUS` | customer |
| `HEARTLAB` | customer |
| `WELLCAN` | customer |

## Layout

| Path | Role |
|------|------|
| `matrix.yaml` | Multi-host pin+where: cells `id`+`erp`+`default_api`+`base_url` (V27); `--cell` selects |
| `config/bootstrap/` | Company, features, credit terms, segmented keys (Bootstrap contract is package SoT — never scaffolded) |
| `config/baseline/` | GL foundation (COA, ledger, subaccounts, UOMs) |
| `config/setup/` | Financial year, master calendar, open periods |
| `config/master/` | Numbering (`05-numbering-sequences`) before module prefs; inventory, warehouse, items, vendors, customers; roles/users (`90-roles` then `91-users`) |
| `scenario/10-seed-capital.yaml` | Once-class owner capital JE (skip-if-present when present); Period = `${current_period}` |
| `scenario/20-buy.yaml` | Additive ingredient PO, then receipt, then bill, then AP pay (four suppliers, kit BOM only) |
| `scenario/30-build.yaml` | Additive kit assembly (ImmunoShield + CardioPure) |
| `scenario/40-sell.yaml` | Additive SO, then ship, then invoice, then AR pay (three brand customers) |
| `config/views/10-trial-balance.yaml` | Observer view (EndingBalance inquire; Period pinned literal; not SEED_DIRS) |
| `state/` | Written by `acu state` (derived-state observations) |

`acu run` expands `${current_period}` to host-local `MMyyyy`. Views for `acu state` stay pinned so committed `state/` rows do not rewrite every month.

Monoscenario `buy-sell` is not part of this package.

## Personas

| User | Role | ERP roles |
| --- | --- | --- |
| `qa-director` | Dr. Elodie Tremblay, Director of QA | IN Manager, PO Viewer |
| `vp-supply-chain` | Marcus Vance, VP Supply Chain | PO Admin, SO Admin |
| `receiving-supervisor` | Devon Singh, Receiving Supervisor | IN Receiver, PO Clerk |
| `erp-architect` | Sophie Archambault, ERP Architect | Administrator |
| `llm-agent` | LLM Agent | LLM Agent |
