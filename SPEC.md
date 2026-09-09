# CanNordic QMS seed

## §G GOAL
Job-function logins on CanNordic QMS seed; humans type function not person; LLM Agent works QM documents; QM master lets Lab5.QMS e2e/UI run.

## §C CONSTRAINTS
- Virgin-tenant `acu` YAML seed (`acu-gitops-qms`); not apply onto half-configured company
- Human FirstName LastName stay current given names
- ERP role bundles stay on same login; not split one login per Rolename
- Username = kebab-case job function; not person initials; not ERP Rolename
- Email local-part = Username; domain `@cannordic.ca`
- Companion customization `acu-custom-qms`; ingestion `acu-google-qms`; CLI defects → `acumatica-cli` not this repo
- Stock rows in `config/master/90-roles.yaml` stay; add custom Rolename `LLM Agent` only
- This repo = seed YAML; not implement QMS screens or ingestion engine; not compile `Lab5.QMS.dll`
- Rebuild = `gmake rebuild` serial delete/create/apply/run/publish/qms/diff/state; never `acu check`
- Quality Manager role + QM RolesInGraph stay in `acu-custom-qms` post-publish; this repo attaches users after that role exists
- `config/qms/` is post-publish only (`QMS/22.200.001` + UsrQMS* + InspectionPlan + Quality Manager + NumberingSequence `QORD` `QNCR`); not SEED_DIRS; virgin `gmake apply` + `gmake run` ! succeed before Lab5.QMS
- Lab5.QMS zip pin in `customization/Lab5.QMS.pin` (GitHub release tag + sha256); bump pin on Lab5.QMS release so rebuilds stay on that package
- User.Roles omit `Selected` (acu ≥ 0.29 / Bootstrap 1.10.0 AssignUser); persist membership in `92-role-users.yaml`
- Company identity in `config/bootstrap/company.yaml`; DecPlQty/WeightUOM/VolumeUOM in `config/baseline/91-company-packaging.yaml` after UOMs

## §I INTERFACES
- yaml: `config/master/91-users.yaml` → User keyed Username; Roles.Rolename (no Selected)
- yaml: `config/master/90-roles.yaml` → Role keyed Rolename
- yaml: `config/master/92-role-users.yaml` → Role.Users persist membership (AssignUser)
- yaml: `config/qms/05-numbering-sequences.yaml` → NumberingSequence `QORD` `QNCR`; endpoint bootstrap; post-publish
- yaml: `config/master/55-lot-serial-classes.yaml` → LotSerialClass `LOTRAW`
- yaml: `config/master/80-stock-items-parts.yaml` → PARTS LotSerialClass `LOTRAW`; no UsrQMS*
- yaml: `config/qms/10-inspection-plans.yaml` → InspectionPlan endpoint `QMS/22.200.001`
- yaml: `config/qms/20-stock-item-qms.yaml` → StockItem endpoint `QMS/22.200.001`; UsrQMSInspectionRequired + PlanID + UsrMinShelfLifeDays
- yaml: `config/qms/30-qm-role-users.yaml` → Quality Manager ← qa-director, llm-agent
- yaml: `scenario/20-buy.yaml` → receipt lines Location `QCHOLD` + LotSerialNbr + ExpirationDate
- yaml: `config/master/51-warehouse-locations.yaml` → WH-MISS-01 Locations `MAIN` `QCHOLD` `READY` `QUARANTINE`
- yaml: `config/master/52-warehouse-defaults.yaml` → ReceivingLocationID `QCHOLD` ShippingLocationID `READY` RMALocationID `QCHOLD`
- yaml: `config/baseline/91-company-packaging.yaml` → Company DecPlQty 3 WeightUOM KG VolumeUOM LITER
- doc: `README.md` Personas table → Username + person + ERP roles; rebuild order tenant delete/create + apply + run + `gmake publish` + post-publish `acu apply config/qms/`; ! `acu check`
- cmd: `gmake apply` seeds SEED_DIRS (`acu apply` ! `config/qms/`); `gmake run` = capital+buy on stock tenant; `acu tenant delete` + `acu tenant create` recreate; `gmake publish` then `gmake qms`; `gmake rebuild` = delete/create/apply/run/publish/qms/diff/state; ! `acu check`
- pin: `customization/Lab5.QMS.pin` → repo tag asset sha256 package endpoint; `gmake publish` deploys `QMS_SRC` at pin version
- map: `etremblay`→`qa-director`, `mvance`→`vp-supply-chain`, `dsingh`→`receiving-supervisor`, `sarchambault`→`erp-architect`; add `llm-agent`

## §V INVARIANTS
V1: login-is-job-function — Username names job function (kebab-case); not person initials
V2: display-name-is-person — human FirstName LastName stay given names (Elodie Tremblay, Marcus Vance, Devon Singh, Sophie Archambault)
V3: erp-roles-stay-bundled — each job-function login keeps current ERP role set; User.Roles omit Selected; 92-role-users Role.Users matches 91-users Roles
V4: llm-agent-qm — Rolename `LLM Agent` + user `llm-agent` works QM documents (inspection orders, CoA files, NCR); not a human persona; FirstName `LLM` LastName `Agent`; post-publish also Quality Manager
V5: email-follows-username — Email = `{Username}@cannordic.ca`
V6: personas-sync — README Personas table Username matches `91-users.yaml`
V7: raw-lot-tracked — features.yaml includes `LotSerialTracking`; PARTS items LotSerialClass `LOTRAW` (Track Lot Numbers, When Received, User-Enterable, TrackExpirationDate, Auto-Incremental segment); KITS items LotSerialClass `NOTRACK` (Not Tracked); ClassID mask alphanumeric no hyphen; buy receipts carry LotSerialNbr + ExpirationDate + Location `QCHOLD`
V8: qms-numbering — NumberingSequence `QORD` `QNCR` in `config/qms/05-numbering-sequences.yaml`; not SEED_DIRS (closes §B.3)
V9: qms-plans-after-publish — `config/qms/10-inspection-plans.yaml` one Active InspectionPlan per raw InventoryID; endpoint `QMS/22.200.001`; not SEED_DIRS
V10: qms-item-flags — `config/qms/20-stock-item-qms.yaml` endpoint `QMS/22.200.001`; sets UsrQMSInspectionRequired + matching PlanID + UsrMinShelfLifeDays on every PARTS item; 80-stock-items-parts.yaml omits UsrQMS* (closes §B.1)
V11: qm-users-after-role — `config/qms/30-qm-role-users.yaml` attaches Quality Manager to qa-director and llm-agent (role seeded by Lab5.QMS)
V12: pinned-lab5-qms — rebuild publishes Lab5.QMS from `customization/Lab5.QMS.pin` (GitHub release tag + sha256) via `QMS_SRC` `lab5-qms deploy`; this repo ! compile DLL ! vendor zip ! `acu check`
V13: qc-ready-locations — WH-MISS-01 Locations `MAIN` `QCHOLD` `READY` `QUARANTINE`; `QCHOLD` ReceiptsAllowed TransfersAllowed SalesAllowed=false AssemblyAllowed=false; `READY` SalesAllowed TransfersAllowed AssemblyAllowed ReceiptsAllowed=false; `QUARANTINE` TransfersAllowed SalesAllowed=false AssemblyAllowed=false ReceiptsAllowed=false; ReceivingLocationID `QCHOLD`; ShippingLocationID `READY`; RMALocationID `QCHOLD`
V14: run-is-capital-buy — `acu run` = `scenario/10-seed-capital.yaml` + `scenario/20-buy.yaml`; no `scenario/30-build.yaml`; no `scenario/40-sell.yaml`; no `config/master/85-kit-specifications.yaml`; no NumberingID `INKITASSY`; INPreferences omits `KitAssemblyNumberingID`
V15: stock-path-without-qms — virgin `gmake apply` + `gmake run` succeed w/ Lab5.QMS unpublished; SEED_DIRS + `scenario/` omit `QMS/22.200.001` UsrQMS* InspectionPlan Quality Manager `QORD` `QNCR`; those live in `config/qms/` post-publish; Makefile rebuild=delete/create/apply/run/publish/qms/diff/state (closes §B.2)

## §T TASKS
id|status|task|cites
T1|x|swap 91-users.yaml Username+Email: etremblay→qa-director, mvance→vp-supply-chain, dsingh→receiving-supervisor, sarchambault→erp-architect; keep FirstName LastName + ERP Roles|V1,V2,V3,V5
T2|x|add Rolename `LLM Agent` in 90-roles.yaml Descr QM documents (inspection orders, CoA files, NCR)|V4
T3|x|add user llm-agent FirstName LLM LastName Agent Email llm-agent@cannordic.ca Roles LLM Agent|V4,V5
T4|x|sync README Personas table to job-function Usernames + llm-agent row|V6
T5|x|sweep leftover personal usernames grep `etremblay|mvance|dsingh|sarchambault`|V1
T6|x|drop Selected from User.Roles; add 92-role-users.yaml matching 91-users membership|V3
T7|x|split Company packaging to baseline/91-company-packaging.yaml after UOMs|I.yaml
T8|x|add NumberingSequence QORD QNCR|V8
T9|x|add LotSerialClass LOTRAW; set on PARTS stock items|V7
T10|x|buy receipts: Location MAIN + LotSerialNbr + ExpirationDate per raw line|V7
T11|x|add config/qms/ InspectionPlan per raw + StockItem UsrQMS* + Quality Manager users|V9,V10,V11
T12|x|README: .env not matrix.yaml; 92-role-users; LOTRAW; post-publish acu apply config/qms/|V6,V7,V9
T13|x|pin Lab5.QMS GitHub release; Makefile rebuild=delete/create/apply/run/publish/qms/diff/state; README drop acu check|V12
T14|x|KITS StockItem LotSerialClass NOTRACK (LotSerialTracking requires a class)|V7
T15|x|kit assembly StockComponents Allocations Location + LotSerialNbr from buy lots|V7
T16|x|add `endpoint: QMS/22.200.001` on `config/qms/20-stock-item-qms.yaml`|V10
T17|x|`acu apply config/qms/20-stock-item-qms.yaml` persists UsrQMS* on all 6 PARTS (no SQL)|V10
T18|x|drop README no-op claim; tests/test_qms.py require stock-item QMS endpoint|V10
T19|x|drop scenario/30-build.yaml + scenario/40-sell.yaml from run|V14
T20|x|add WH-MISS-01 Locations QCHOLD READY; warehouse defaults Receiving QCHOLD Shipping READY RMA QCHOLD|V13
T21|x|buy receipts Location QCHOLD; tests + README run=capital+buy|V7,V13,V14,I.yaml
T22|x|add WH-MISS-01 Location QUARANTINE (failed inspection); tests + README|V13,I.yaml
T23|x|drop `config/master/85-kit-specifications.yaml` + NumberingID `INKITASSY` + INPreferences `KitAssemblyNumberingID`; tests + README|V14
T24|x|patch Makefile rebuild=delete/create/apply/run/publish/qms/diff/state; apply ! config/qms; grep SEED_DIRS+scenario `QMS/22.200.001|UsrQMS|entity: InspectionPlan|Rolename: Quality Manager` → 0 hits; tests + README order|V15,I.cmd
T25|.|move NumberingSequence QORD QNCR to config/qms/05-numbering-sequences.yaml; Makefile qms apply dir; grep SEED_DIRS+scenario QORD QNCR → 0 hits; tests + README|V8,V15,B3

## §B BUGS
id|date|cause|fix
B1|2026-09-07|20-stock-item-qms.yaml missing endpoint → Default StockItem ignores UsrQMS*|V10
B2|2026-09-09|stock apply/run mixed QMS-only YAML or Makefile ran run after qms → virgin tenant w/o Lab5.QMS fails|V15
B3|2026-09-09|QORD QNCR in master NumberingSequence → virgin apply 422 NewSymbol (QMS-only insert)|V8,V15
