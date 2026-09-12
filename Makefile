ifeq ($(filter notintermediate,$(.FEATURES)),)
$(error GNU Make ≥ 4.4 required (this is $(MAKE_VERSION) from $(MAKE)). On macOS: brew install make && gmake <target>)
endif

.SILENT:

SHELL := /bin/sh
MAKEFLAGS += --no-builtin-rules --no-builtin-variables

empty :=
space := $(empty) $(empty)
s := $(shell printf '\036')
esc := $(shell printf '\033')
blue := $(esc)[34m
green := $(esc)[32m
yellow := $(esc)[33m
reset := $(esc)[0m

header = $(info $(blue)==> $1 <==$(reset))

# Short flags live in the first MAKEFLAGS word (`nprR`). `-n` is `n` there;
# later words (`--jobserver-auth=...`) also contain `n` and must be ignored.
dry-run = $(findstring n,$(firstword $(MAKEFLAGS)))

# Sibling customization checkout. Override: gmake qms-publish QMS_SRC=/path/to/acu-custom-qms
QMS_SRC ?= $(abspath ../acu-custom-qms)
PIN := customization/Lab5.QMS.pin
CACHE := .cache

pin-kv := $(foreach w,$(file < $(PIN)),$(if $(and $(findstring =,$(w)),$(filter-out \#%,$(w))),$(w)))
pin-val = $(or $(patsubst $1=%,%,$(filter $1=%,$(pin-kv))),$(error $(PIN): missing $1))
QMS_REPO := $(call pin-val,repo)
QMS_TAG := $(call pin-val,tag)
QMS_ASSET := $(call pin-val,asset)
QMS_SHA256 := $(call pin-val,sha256)
QMS_PACKAGE := $(call pin-val,package)
QMS_ENDPOINT := $(call pin-val,endpoint)
PIN_VERSION := $(patsubst v%,%,$(QMS_TAG))
src-version = $(shell cd "$(QMS_SRC)" && uv version --short)

TENANT := $(patsubst ACU_TENANT=%,%,$(filter ACU_TENANT=%,$(file < .env)))

need-env = $(if $(dry-run),,$(if $(wildcard .env),,$(error .env missing — decrypt .env.gpg at the repo root)))
need-acu = $(if $(dry-run),,$(if $(shell command -v acu),,$(error acu not on PATH — uv tool install acumatica-cli)))
need-gh = $(if $(dry-run),,$(if $(shell command -v gh),,$(error gh CLI required — https://cli.github.com/)))
need-qms-src = $(if $(dry-run),,$(if $(wildcard $(QMS_SRC)/.),,$(error QMS_SRC missing: $(QMS_SRC) — clone $(QMS_REPO) or pass QMS_SRC=)))
need-pin-match = $(if $(dry-run),,$(if $(filter $(PIN_VERSION),$(src-version)),,$(error QMS_SRC version $(src-version) != pin $(PIN_VERSION) ($(PIN)) — checkout $(QMS_TAG) in $(QMS_SRC) or gmake qms-update)))

default: help

.PHONY: help test rebuild
.PHONY: acu-preflight acu-delete acu-create acu-apply acu-run acu-diff acu-state
.PHONY: qms-publish qms-fetch qms-update qms-apply
.PHONY: _qms-fetch-download _qms-fetch-verify

###############################################################################
# Tests
###############################################################################

test: ## Local unit tests (no live tenant)
	$(call header,Running unit tests)
	python3 -m unittest discover -s tests -p 'test_*.py' -v

###############################################################################
# Acu — tenant + seed (no Lab5.QMS)
###############################################################################

acu-preflight: ## Read-only acu config check against .env
	$(call need-env)
	$(call need-acu)
	$(call header,acu config check)
	acu config check

acu-delete: acu-preflight ## Delete ACU_TENANT (irreversible)
	$(call header,Deleting tenant $(TENANT))
	acu tenant delete --login "$(TENANT)" --yes

acu-create: ## Create ACU_TENANT + first-login + AcuBootstrap
	$(call header,Creating tenant $(TENANT))
	acu tenant create --login "$(TENANT)"

acu-apply: ## Seed config/ bootstrap → baseline → setup → master
	$(call header,acu apply)
	acu apply

acu-run: ## Lifecycle scenarios (capital → buy)
	$(call header,acu run)
	acu run

acu-diff: ## Prove SEED_DIRS have no drift (config/qms/ is post-publish)
	$(call header,acu diff)
	acu diff

acu-state: ## Capture derived-state observations into state/
	$(call header,acu state)
	acu state

###############################################################################
# QMS — Lab5.QMS pin, zip, publish, post-publish seed
###############################################################################

# Publish the pinned Lab5.QMS zip. Prefers a sibling checkout at the pin tag
# (same .env tenant). This repo never compiles the DLL.
qms-publish: ## Publish pinned Lab5.QMS from QMS_SRC (acuqms deploy)
	$(call need-qms-src)
	$(call need-pin-match)
	$(call header,acuqms deploy $(QMS_TAG) from $(QMS_SRC))
	cd "$(QMS_SRC)" && uv run acuqms deploy

qms-fetch: _qms-fetch-download .WAIT _qms-fetch-verify ## Download the pinned GitHub-release zip into .cache/ and verify sha256
	:

_qms-fetch-download:
	$(call need-gh)
	mkdir -p "$(CACHE)"
	$(call header,Fetching $(QMS_ASSET) $(QMS_TAG))
	gh release download "$(QMS_TAG)" \
		--repo "$(QMS_REPO)" \
		--pattern "$(QMS_ASSET)" \
		--dir "$(CACHE)" \
		--clobber

_qms-fetch-verify:
	$(if $(dry-run),,$(let got,$(firstword $(shell shasum -a 256 $(CACHE)/$(QMS_ASSET))),\
		$(if $(filter $(QMS_SHA256),$(got)),$(info $(CACHE)/$(QMS_ASSET)),\
			$(error sha256 mismatch for $(CACHE)/$(QMS_ASSET) (pin $(QMS_SHA256), got $(got))))))
	:

# Resolve the latest GitHub release, rewrite pin tag+sha256, download the zip.
# Pin keys other than tag/sha256 are left untouched. Not part of rebuild —
# rebuild publishes whatever the pin already names.
qms-update: ## Bump Lab5.QMS.pin to latest GitHub release and download the zip
	$(call need-gh)
	$(call header,Latest Lab5.QMS release → $(PIN) + $(CACHE)/$(QMS_ASSET))
	set -e; \
	repo="$(QMS_REPO)"; \
	asset="$(QMS_ASSET)"; \
	pin="$(PIN)"; \
	cache="$(CACHE)"; \
	tag=$$(gh release view --repo "$$repo" --json tagName --jq .tagName); \
	if [ -z "$$tag" ]; then echo "error: no latest release for $$repo" >&2; exit 1; fi; \
	mkdir -p "$$cache"; \
	echo "Fetching $$asset $$tag"; \
	gh release download "$$tag" \
		--repo "$$repo" \
		--pattern "$$asset" \
		--dir "$$cache" \
		--clobber; \
	got=$$(shasum -a 256 "$$cache/$$asset"); \
	got=$${got%% *}; \
	digest=$$(gh release view "$$tag" --repo "$$repo" --json assets --jq ".assets[] | select(.name==\"$$asset\") | .digest"); \
	want=$$got; \
	case "$$digest" in sha256:*) want=$${digest#sha256:};; "") want=$$got;; *) want=$$digest;; esac; \
	if [ "$$got" != "$$want" ]; then echo "error: sha256 mismatch for $$cache/$$asset (release $$want, got $$got)" >&2; exit 1; fi; \
	awk -v tag="$$tag" -v sha="$$got" 'BEGIN{t=0;s=0} /^tag=/{print "tag=" tag; t=1; next} /^sha256=/{print "sha256=" sha; s=1; next} {print} END{if(!t||!s) exit 1}' "$$pin" > "$$cache/pin.tmp"; \
	mv "$$cache/pin.tmp" "$$pin"; \
	echo "$$pin $$tag sha256=$$got"; \
	echo "$$cache/$$asset"

qms-apply: ## Post-publish QMS master (QORD/QNCR numbering + inspection plans + UsrQMS* + Quality Manager)
	$(call header,acu apply config/qms/)
	acu apply config/qms/

###############################################################################
# Rebuild — never `acu check` (subcommand is going away)
###############################################################################

rebuild: acu-delete .WAIT acu-create .WAIT acu-apply .WAIT acu-run .WAIT qms-publish .WAIT qms-apply .WAIT acu-diff .WAIT acu-state ## Full CNBN recreate + pinned Lab5.QMS (apply then run before publish; serial; never acu check)
	$(call header,rebuild green on $(TENANT))

###############################################################################
# Help
###############################################################################

# Target-line double-hash descriptions, read with $(file) and split with $(let).
help-src := $(file < $(firstword $(MAKEFILE_LIST)))
help-words := $(foreach w,$(subst $(space),$(s),$(help-src)),$(if $(and $(findstring $(s)##$(s),$(w)),$(filter-out \#%,$(w))),$(w)))
help-name = $(let tgt desc,$(subst $(s)##$(s), ,$1),$(patsubst %:,%,$(firstword $(subst $(s),$(space),$(tgt)))))
help-acu = $(foreach w,$(help-words),$(if $(filter acu-%,$(call help-name,$(w))),$(w)))
help-qms = $(foreach w,$(help-words),$(if $(filter qms-%,$(call help-name,$(w))),$(w)))
help-other = $(foreach w,$(help-words),$(if $(filter acu-% qms-%,$(call help-name,$(w))),,$(w)))
show-help = $(let tgt desc,$(subst $(s)##$(s), ,$1),$(let name text,$(patsubst %:,%,$(firstword $(subst $(s),$(space),$(tgt)))) $(strip $(subst $(s),$(space),$(desc))),$(info   $(yellow)$(shell printf '%-14s' '$(name)')$(reset) $(text))))

help:
	$(info $(blue)Usage: $(green)gmake [recipe]$(reset))
	$(info $(blue)Pinned Lab5.QMS:$(reset) $(QMS_TAG) ($(QMS_PACKAGE) $(QMS_ENDPOINT)))
	$(info $(blue)QMS_SRC:$(reset) $(QMS_SRC))
	$(info $(blue)Acu:$(reset))
	$(foreach w,$(sort $(help-acu)),$(call show-help,$(w)))
	$(info $(blue)QMS:$(reset))
	$(foreach w,$(sort $(help-qms)),$(call show-help,$(w)))
	$(info $(blue)Other:$(reset))
	$(foreach w,$(sort $(help-other)),$(call show-help,$(w)))
	:
