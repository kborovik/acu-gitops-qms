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

`acu tenant create` publishes AcuBootstrap so
Company maps CS101500 `DecPlQty` (this seed sets 3 for milligram-scale KG
kit BOMs), SegmentedKey maps `Length` to CS202000 `Detail`, and Role
`AssignUser` persists `UsersInRoles`. Do not use `acu check` (cold-lifecycle
subcommand; going away).

## Rebuild order

One shot: `gmake rebuild`. Steps:

```sh
# 1. Credentials in .env (ACU_PASSWORD, ACU_TENANT, ACU_BASE_URL, ACU_API_VERSION)
acu config check

# 2. Recreate empty tenant (create = first-login + AcuBootstrap)
acu tenant delete --login CNBN --yes
acu tenant create --login CNBN

# 3. Seed config umbrella (bootstrap → baseline → setup → master)
acu apply

# 4. Lifecycle scenarios (once capital → buy → build → sell)
acu run

# 5. Publish pinned Lab5.QMS (sibling checkout at pin tag; this repo does not compile)
gmake publish
# pin: customization/Lab5.QMS.pin → GitHub release kborovik/acu-custom-qms
# override checkout: gmake publish QMS_SRC=/path/to/acu-custom-qms

# 6. Post-publish: inspection plans + UsrQMS* + Quality Manager users
acu apply config/qms/

# 7. Prove no drift (SEED_DIRS only; config/qms/ is post-publish)
acu diff

# 8. Capture derived-state observations (EndingBalance trial-balance)
acu state
# warm gate: once-capital only — additive buy/sell moves numeric observations
acu run scenario/10-seed-capital.yaml && acu state --assert-unchanged

# Optional: re-seed from live (inverse of apply; always under config/)
# acu extract --out . --force
```

Bare `acu apply` / `acu diff` also prefer `config/` when those trees exist.
`acu extract` hard-cuts emit to `config/{bootstrap,baseline,setup,master}/` (never root SEED_DIRS).
`config/qms/` is not a SEED_DIR — apply it only after Lab5.QMS is published.

Lab5.QMS is not compiled here. `customization/Lab5.QMS.pin` names the GitHub
release zip (`tag` + `sha256`). `gmake publish` runs `lab5-qms deploy` from
`QMS_SRC` (default `../acu-custom-qms`) only when that checkout's version
matches the pin. `gmake fetch` downloads the release asset into `.cache/`
and checks the digest. Bump the pin when `acu-custom-qms` ships a new
release — that is how a tenant rebuild stays on the same customization.

InspectionPlan GET works on `QMS/22.200.001`. PUT currently 500s (`QMSInspectionPlan` synonym schema cache) — seed plans via SQL or the QM.20.10.00 screen until that PUT is fixed in Lab5.QMS. Default `StockItem` ignores `UsrQMS*` on PUT (fields are not on the Default contract); set them with SQL after publish. `acu apply config/qms/20-stock-item-qms.yaml` is a no-op until that mapping exists. `config/qms/30-qm-role-users.yaml` applies.

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
| `RAW-ECH-EXT4` | raw (lot `LOTRAW`, plan `PLAN-ECH-EXT4`) |
| `RAW-ELD-EXT10` | raw (lot `LOTRAW`, plan `PLAN-ELD-EXT10`) |
| `RAW-ASH-EXT5` | raw (lot `LOTRAW`, plan `PLAN-ASH-EXT5`) |
| `RAW-COQ10-99` | raw (lot `LOTRAW`, plan `PLAN-COQ10-99`) |
| `RAW-OMEGA3-70` | raw (lot `LOTRAW`, plan `PLAN-OMEGA3-70`) |
| `RAW-ASTA-10` | raw (lot `LOTRAW`, plan `PLAN-ASTA-10`) |
| `FG-IMMUNE-DEFENSE-60C` | kit |
| `FG-CARDIO-OMEGA-COQ10-60SG` | kit |
| `VITALPLUS` | customer |
| `HEARTLAB` | customer |
| `WELLCAN` | customer |
| `LOTRAW` | lot/serial class for raw (When Received, user-enterable, expiry) |
| `NOTRACK` | lot/serial class for kits (Not Tracked; required while LotSerialTracking is on) |
| `QORD` / `QNCR` | numbering (inspection orders / NCR) |

## Layout

| Path | Role |
|------|------|
| `.env` | Secrets + REST where (`ACU_BASE_URL`) + Default pin (`ACU_API_VERSION`) |
| `customization/Lab5.QMS.pin` | Pinned Lab5.QMS GitHub release (tag + sha256). Not the zip |
| `Makefile` | `gmake rebuild` / `publish` / `qms` — never `acu check` |
| `config/bootstrap/` | Company identity, features, credit terms, segmented keys (Bootstrap contract is package SoT — never scaffolded) |
| `config/baseline/` | GL foundation (COA, ledger, subaccounts, UOMs, company packaging `91-company-packaging`) |
| `config/setup/` | Financial year, master calendar, open periods |
| `config/master/` | Numbering (`05-numbering-sequences` includes `QORD`/`QNCR`) before module prefs; `LOTRAW`; inventory, warehouse, items, vendors, customers; roles/users (`90-roles` then `91-users` then `92-role-users`) |
| `config/qms/` | Post-publish Lab5.QMS: inspection plans, StockItem UsrQMS*, Quality Manager user attach. Not SEED_DIRS |
| `scenario/10-seed-capital.yaml` | Once-class owner capital JE (skip-if-present when present); Period = `${current_period}` |
| `scenario/20-buy.yaml` | Additive ingredient PO, then receipt (lot + expiry), then bill, then AP pay (four suppliers, kit BOM only) |
| `scenario/30-build.yaml` | Additive kit assembly (ImmunoShield + CardioPure) |
| `scenario/40-sell.yaml` | Additive SO, then ship, then invoice, then AR pay (three brand customers) |
| `config/views/10-trial-balance.yaml` | Observer view (EndingBalance inquire; Period pinned literal; not SEED_DIRS) |
| `state/` | Written by `acu state` (derived-state observations) |

`acu run` expands `${current_period}` to host-local `MMyyyy`. Views for `acu state` stay pinned so committed `state/` rows do not rewrite every month.

Monoscenario `buy-sell` is not part of this package.

## Personas

| User | Role | ERP roles |
| --- | --- | --- |
| `qa-director` | Dr. Elodie Tremblay, Director of QA | IN Manager, PO Viewer (+ Quality Manager after `config/qms/`) |
| `vp-supply-chain` | Marcus Vance, VP Supply Chain | PO Admin, SO Admin |
| `receiving-supervisor` | Devon Singh, Receiving Supervisor | IN Receiver, PO Clerk |
| `erp-architect` | Sophie Archambault, ERP Architect | Administrator |
| `llm-agent` | LLM Agent | LLM Agent (+ Quality Manager after `config/qms/`) |
