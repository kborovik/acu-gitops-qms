# CanNordic QMS seed

## §G GOAL
Job-function logins on CanNordic QMS seed; humans type function not person; LLM Agent works QM documents.

## §C CONSTRAINTS
- Virgin-tenant `acu` YAML seed (`acu-gitops-qms`); not apply onto half-configured company
- Human FirstName LastName stay current given names
- ERP role bundles stay on same login; not split one login per Rolename
- Username = kebab-case job function; not person initials; not ERP Rolename
- Email local-part = Username; domain `@cannordic.ca`
- Companion customization `acu-custom-qms`; ingestion `acu-google-qms`; CLI defects → `acumatica-cli` not this repo
- Stock rows in `config/master/90-roles.yaml` stay; add custom Rolename `LLM Agent` only
- This repo = seed YAML; not implement QMS screens or ingestion engine

## §I INTERFACES
- yaml: `config/master/91-users.yaml` → User keyed Username; Roles.Rolename
- yaml: `config/master/90-roles.yaml` → Role keyed Rolename
- doc: `README.md` Personas table → Username + person + ERP roles
- cmd: `acu apply` seeds roles then users after bootstrap
- map: `etremblay`→`qa-director`, `mvance`→`vp-supply-chain`, `dsingh`→`receiving-supervisor`, `sarchambault`→`erp-architect`; add `llm-agent`

## §V INVARIANTS
V1: login-is-job-function — Username names job function (kebab-case); not person initials
V2: display-name-is-person — human FirstName LastName stay given names (Elodie Tremblay, Marcus Vance, Devon Singh, Sophie Archambault)
V3: erp-roles-stay-bundled — each job-function login keeps current ERP role set
V4: llm-agent-qm — Rolename `LLM Agent` + user `llm-agent` works QM documents (inspection orders, CoA files, NCR); not a human persona; FirstName `LLM` LastName `Agent`
V5: email-follows-username — Email = `{Username}@cannordic.ca`
V6: personas-sync — README Personas table Username matches `91-users.yaml`

## §T TASKS
id|status|task|cites
T1|x|swap 91-users.yaml Username+Email: etremblay→qa-director, mvance→vp-supply-chain, dsingh→receiving-supervisor, sarchambault→erp-architect; keep FirstName LastName + ERP Roles|V1,V2,V3,V5
T2|.|add Rolename `LLM Agent` in 90-roles.yaml Descr QM documents (inspection orders, CoA files, NCR)|V4
T3|.|add user llm-agent FirstName LLM LastName Agent Email llm-agent@cannordic.ca Roles LLM Agent|V4,V5
T4|.|sync README Personas table to job-function Usernames + llm-agent row|V6
T5|.|sweep leftover personal usernames grep `etremblay|mvance|dsingh|sarchambault`|V1

## §B BUGS
id|date|cause|fix
