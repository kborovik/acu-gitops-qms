# AGENTS.md

This repo is an `acu` data package (YAML seed). The CLI lives in
[`kborovik/acumatica-cli`](https://github.com/kborovik/acumatica-cli). Do not
patch the CLI from here.

## acu CLI defects — file upstream

When `acu` errors, crashes, or lacks a command, flag, entity, or capability
needed to finish work in this repo, open a GitHub issue on
**kborovik/acumatica-cli**. Do not open that issue on this repo.

1. Search first:

   ```sh
   gh issue list --repo kborovik/acumatica-cli --state all --search "<summary>"
   ```

2. If none matches, create the issue:

   ```sh
   gh issue create --repo kborovik/acumatica-cli \
     --title "<one-line summary>" \
     --body "$(cat <<'EOF'
   <symptom in the first sentence>

   Command, flags, cwd, and exit code. Paste the error. Note the workaround if any.

   ## Acceptance

   - [ ] <observable fix>
   EOF
   )"
   ```

3. Paste the new issue URL in the session reply.

File here only for seed YAML, company data, or layout problems in this repo.

Counts as an upstream issue:

- CLI crash, unexpected error, or wrong exit code
- Missing command, flag, seed entity, or capability this package needs
- `apply` / `diff` / `run` / `extract` / `state` / `bootstrap` / `config` behavior that does not match the CLI docs

Does not:

- Invalid YAML or wrong IDs in this repo
- Tenant, network, or credential failures
- A gap already tracked (for example [acumatica-cli#30](https://github.com/kborovik/acumatica-cli/issues/30))
