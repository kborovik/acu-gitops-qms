# CanNordic BioNutra Inc. (`acu` data repo)

Virgin-tenant Acumatica seed for **CanNordic BioNutra Inc.** (AcctCD `CNBN`), a
Canadian CDMO and ingredient importer (NHPs, functional foods). Finance +
inventory/distribution + kit assembly. Single full seed — no `--flavor`.

Sourced from the company profile and master data in
[`gcp-acu-coa`](../gcp-acu-coa/domain/COMPANY_PROFILE.md). Seed IDs are
shortened to virgin-tenant segmented-key length (10). Domain IDs stay in the
mapping table below.

**Start from a brand-new empty tenant.** Do not apply onto a half-configured company.

## Rebuild order

```sh
# 1. Credentials in .env (ACU_PASSWORD, ACU_TENANT, …)
#    Default API pin + REST where = committed matrix.yaml cell
#    (default_api + base_url; not sticky ACU_BASE_URL / ACU_API_VERSION)
acu config check

# 2. Publish Bootstrap (features + contract from config/bootstrap/)
acu bootstrap

# 3. Seed config umbrella (bootstrap → baseline → setup → master)
#    bare `acu apply` also appends overlays/default-<default_api>/ when present
acu apply

# 4. Lifecycle scenarios (once capital → buy → build → sell)
#    bare `acu run` replaces same-name files from pin overlay scenario/
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

Warehouses: `WHMISS` (plant + QC bays), `WHQC` (Saint-Laurent), `WHBC` (BC).
Buy / build / sell run on `WHMISS` / `MAIN`. QC hold bays (`QCHOLDA/B/C`, `COLD`, `FG`) exist for the inbound CoA story; lot/serial class is not seeded (CLI demo non-goal).

## Domain ID map

Virgin segmented keys are 10 characters. Domain catalog IDs longer than that
are shortened here; CoA ingestion should use the seed column.

| Domain | Seed | Kind |
| --- | --- | --- |
| CanNordic BioNutra Inc. | `CNBN` | company |
| WH-MISS-01 | `WHMISS` | warehouse |
| WH-MISS-COLD-01 | `WHMISS` / `COLD` | location |
| WH-MISS-FG-01 | `WHMISS` / `FG` | location |
| QC-HOLD-BAY-A/B/C | `QCHOLDA` / `QCHOLDB` / `QCHOLDC` | location |
| VEND-NORTH-BIO | `NORTHBIO` | vendor |
| VEND-ALPINE-EXT | `ALPINE` | vendor |
| VEND-PACIFIC-ORG | `PACIFIC` | vendor |
| VEND-NIPPON-PHARMA | `NIPPON` | vendor |
| VEND-NORDIC-MAR | `NORDIC` | vendor |
| LAB-GL-ANALYTICAL | `GLAKES` | lab vendor |
| LAB-EURO-PHYTO | `EUROPHYTO` | lab vendor |
| LAB-PACIFIC-TEST | `PACLAB` | lab vendor |
| LAB-TOKYO-BIO | `TOKYOBIO` | lab vendor |
| LAB-FJORD-ANALYTICAL | `FJORD` | lab vendor |
| RAW-ECH-EXT4 | `ECHEXT4` | raw |
| RAW-ELD-EXT10 | `ELDEXT10` | raw |
| RAW-ASH-EXT5 | `ASHEXT5` | raw |
| RAW-RHOD-EXT3 | `RHODEXT3` | raw |
| RAW-CURC-95 | `CURC95` | raw |
| RAW-GUT-PRB100 | `PRB100` | raw |
| RAW-COQ10-99 | `COQ1099` | raw |
| RAW-THEA-98 | `THEA98` | raw |
| RAW-OMEGA3-70 | `OMEGA370` | raw |
| RAW-ASTA-10 | `ASTA10` | raw |
| FG-IMMUNE-DEFENSE-60C | `IMMUNE60` | kit |
| FG-CARDIO-OMEGA-COQ10-60SG | `CARDIO60` | kit |

Kit specs follow the domain BOMs (mg/capsule × 60, as KG per bottle):
ImmunoShield `0.012` + `0.009` + `0.006` KG; CardioPure `0.060` + `0.006` + `0.001` KG.

Item class IDs stay `PARTS` / `KITS` so `acu extract` filter-split still matches.

## Layout

| Path | Role |
|------|------|
| `matrix.yaml` | Multi-host pin+where: cells `id`+`erp`+`default_api`+`base_url` (V27); `--cell` selects |
| `config/bootstrap/` | Company, features, credit terms (Bootstrap contract is package SoT — never scaffolded) |
| `config/baseline/` | GL foundation (COA, ledger, subaccounts, UOMs) |
| `config/setup/` | Financial year, master calendar, open periods |
| `config/master/` | Numbering (`05-numbering-sequences`) before module prefs; inventory, warehouse, items, vendors, customers; roles/users (`90-roles` then `91-users`) |
| `scenario/10-seed-capital.yaml` | Once-class owner capital JE (skip-if-present when present); Period = `${current_period}` |
| `scenario/20-buy.yaml` | Additive ingredient PO → receipt → bill → AP pay (five suppliers) |
| `scenario/30-build.yaml` | Additive kit assembly (ImmunoShield + CardioPure) |
| `scenario/40-sell.yaml` | Additive SO → ship → invoice → AR pay (three brand customers) |
| `overlays/` | Default-half rewrites (`default-<default_api>/`); bare apply/run/diff auto-compose |
| `overlays/default-24.200.001/` | Lab 25r1 half: KitAssembly Type Assembly |
| `config/views/10-trial-balance.yaml` | Observer view (EndingBalance inquire; Period pinned literal; not SEED_DIRS) |
| `state/` | Written by `acu state` (derived-state observations) |

`acu run` expands `${current_period}` to host-local `MMyyyy`. Views for `acu state` stay pinned so committed `state/` rows do not rewrite every month.

Monoscenario `buy-sell` is not part of this package.

## Personas

| User | Role | ERP roles |
| --- | --- | --- |
| `etremblay` | Dr. Elodie Tremblay, Director of QA | IN Manager, PO Viewer |
| `mvance` | Marcus Vance, VP Supply Chain | PO Admin, SO Admin |
| `dsingh` | Devon Singh, Receiving Supervisor | IN Receiver, PO Clerk |
| `sarchambault` | Sophie Archambault, ERP Architect | Administrator |
| `soadmin` | Sales order admin | SO Admin |
