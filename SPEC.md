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
- This repo = seed YAML; not implement QMS screens or ingestion engine
- Quality Manager role + QM RolesInGraph stay in `acu-custom-qms` post-publish; this repo attaches users after that role exists
- `config/qms/` is post-publish only (`QMS/22.200.001` + UsrQMS* on StockItem); not SEED_DIRS; virgin `acu apply` must succeed before Lab5.QMS
- User.Roles omit `Selected` (acu ≥ 0.29 / Bootstrap 1.10.0 AssignUser); persist membership in `92-role-users.yaml`
- Company identity in `config/bootstrap/company.yaml`; DecPlQty/WeightUOM/VolumeUOM in `config/baseline/91-company-packaging.yaml` after UOMs

## §I INTERFACES
- yaml: `config/master/91-users.yaml` → User keyed Username; Roles.Rolename (no Selected)
- yaml: `config/master/90-roles.yaml` → Role keyed Rolename
- yaml: `config/master/92-role-users.yaml` → Role.Users persist membership (AssignUser)
- yaml: `config/master/05-numbering-sequences.yaml` → QORD QNCR
- yaml: `config/master/55-lot-serial-classes.yaml` → LotSerialClass `LOTRAW`
- yaml: `config/master/80-stock-items-parts.yaml` → PARTS LotSerialClass `LOTRAW`; no UsrQMS*
- yaml: `config/qms/10-inspection-plans.yaml` → InspectionPlan endpoint `QMS/22.200.001`
- yaml: `config/qms/20-stock-item-qms.yaml` → StockItem UsrQMSInspectionRequired + PlanID + UsrMinShelfLifeDays
- yaml: `config/qms/30-qm-role-users.yaml` → Quality Manager ← qa-director, llm-agent
- yaml: `scenario/20-buy.yaml` → receipt lines Location + LotSerialNbr + ExpirationDate
- yaml: `config/baseline/91-company-packaging.yaml` → Company DecPlQty 3 WeightUOM KG VolumeUOM LITER
- doc: `README.md` Personas table → Username + person + ERP roles; rebuild order `.env` + post-publish `acu apply config/qms/`
- cmd: `acu apply` seeds SEED_DIRS; `acu apply config/qms/` after Lab5.QMS publish
- map: `etremblay`→`qa-director`, `mvance`→`vp-supply-chain`, `dsingh`→`receiving-supervisor`, `sarchambault`→`erp-architect`; add `llm-agent`

## §V INVARIANTS
V1: login-is-job-function — Username names job function (kebab-case); not person initials
V2: display-name-is-person — human FirstName LastName stay given names (Elodie Tremblay, Marcus Vance, Devon Singh, Sophie Archambault)
V3: erp-roles-stay-bundled — each job-function login keeps current ERP role set; User.Roles omit Selected; 92-role-users Role.Users matches 91-users Roles
V4: llm-agent-qm — Rolename `LLM Agent` + user `llm-agent` works QM documents (inspection orders, CoA files, NCR); not a human persona; FirstName `LLM` LastName `Agent`; post-publish also Quality Manager
V5: email-follows-username — Email = `{Username}@cannordic.ca`
V6: personas-sync — README Personas table Username matches `91-users.yaml`
V7: raw-lot-tracked — features.yaml includes `LotSerialTracking`; PARTS items LotSerialClass `LOTRAW` (Track Lot Numbers, When Received, User-Enterable, TrackExpirationDate, Auto-Incremental segment); ClassID mask alphanumeric no hyphen; buy receipts carry LotSerialNbr + ExpirationDate + Location
V8: qms-numbering — NumberingSequence `QORD` `QNCR` in `05-numbering-sequences.yaml`
V9: qms-plans-after-publish — `config/qms/10-inspection-plans.yaml` one Active InspectionPlan per raw InventoryID; endpoint `QMS/22.200.001`; not SEED_DIRS
V10: qms-item-flags — `config/qms/20-stock-item-qms.yaml` sets UsrQMSInspectionRequired + matching PlanID + UsrMinShelfLifeDays on every PARTS item; 80-stock-items-parts.yaml omits UsrQMS*
V11: qm-users-after-role — `config/qms/30-qm-role-users.yaml` attaches Quality Manager to qa-director and llm-agent (role seeded by Lab5.QMS)

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

## §B BUGS
id|date|cause|fix
