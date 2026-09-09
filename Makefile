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

# Sibling customization checkout. Override: gmake publish QMS_SRC=/path/to/acu-custom-qms
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
need-pin-match = $(if $(dry-run),,$(if $(filter $(PIN_VERSION),$(src-version)),,$(error QMS_SRC version $(src-version) != pin $(PIN_VERSION) ($(PIN)) — checkout $(QMS_TAG) in $(QMS_SRC) or bump the pin after a Lab5.QMS release)))

default: help

.PHONY: help preflight rebuild delete create apply run publish fetch qms diff state test
.PHONY: _fetch-download _fetch-verify

###############################################################################
# Tests
###############################################################################

test: ## Local unit tests (no live tenant)
	$(call header,Running unit tests)
	python3 -m unittest discover -s tests -p 'test_*.py' -v

###############################################################################
# Rebuild — never `acu check` (subcommand is going away)
###############################################################################

preflight: ## Read-only acu config check against .env
	$(call need-env)
	$(call need-acu)
	$(call header,acu config check)
	acu config check

delete: preflight ## Delete ACU_TENANT (irreversible)
	$(call header,Deleting tenant $(TENANT))
	acu tenant delete --login "$(TENANT)" --yes

create: ## Create ACU_TENANT + first-login + AcuBootstrap
	$(call header,Creating tenant $(TENANT))
	acu tenant create --login "$(TENANT)"

apply: ## Seed config/{bootstrap,baseline,setup,master}/
	$(call header,acu apply)
	acu apply

run: ## Lifecycle scenarios (capital → buy)
	$(call header,acu run)
	acu run

# Publish the pinned Lab5.QMS zip. Prefers a sibling checkout at the pin tag
# (same .env tenant). This repo never compiles the DLL.
publish: ## Publish pinned Lab5.QMS from QMS_SRC (lab5-qms deploy)
	$(call need-qms-src)
	$(call need-pin-match)
	$(call header,lab5-qms deploy $(QMS_TAG) from $(QMS_SRC))
	cd "$(QMS_SRC)" && uv run lab5-qms deploy

fetch: _fetch-download .WAIT _fetch-verify ## Download the pinned GitHub-release zip into .cache/ and verify sha256
	:

_fetch-download:
	$(call need-gh)
	mkdir -p "$(CACHE)"
	$(call header,Fetching $(QMS_ASSET) $(QMS_TAG))
	gh release download "$(QMS_TAG)" \
		--repo "$(QMS_REPO)" \
		--pattern "$(QMS_ASSET)" \
		--dir "$(CACHE)" \
		--clobber

_fetch-verify:
	$(if $(dry-run),,$(let got,$(firstword $(shell shasum -a 256 $(CACHE)/$(QMS_ASSET))),\
		$(if $(filter $(QMS_SHA256),$(got)),$(info $(CACHE)/$(QMS_ASSET)),\
			$(error sha256 mismatch for $(CACHE)/$(QMS_ASSET) (pin $(QMS_SHA256), got $(got))))))
	:

qms: ## Post-publish QMS master (QORD/QNCR numbering + inspection plans + UsrQMS* + Quality Manager)
	$(call header,acu apply config/qms/)
	acu apply config/qms/

diff: ## Prove SEED_DIRS have no drift (config/qms/ is post-publish)
	$(call header,acu diff)
	acu diff

state: ## Capture derived-state observations into state/
	$(call header,acu state)
	acu state

rebuild: delete .WAIT create .WAIT apply .WAIT run .WAIT publish .WAIT qms .WAIT diff .WAIT state ## Full CNBN recreate + pinned Lab5.QMS (apply then run before publish; serial; never acu check)
	$(call header,rebuild green on $(TENANT))

###############################################################################
# Help
###############################################################################

# Target-line double-hash descriptions, read with $(file) and split with $(let).
help-src := $(file < $(firstword $(MAKEFILE_LIST)))
help-words := $(foreach w,$(subst $(space),$(s),$(help-src)),$(if $(and $(findstring $(s)##$(s),$(w)),$(filter-out \#%,$(w))),$(w)))
pad-apply := apply$(space)$(space)$(space)$(space)$(space)
pad-create := create$(space)$(space)$(space)$(space)
pad-delete := delete$(space)$(space)$(space)$(space)
pad-diff := diff$(space)$(space)$(space)$(space)$(space)$(space)
pad-fetch := fetch$(space)$(space)$(space)$(space)$(space)
pad-preflight := preflight$(space)
pad-publish := publish$(space)$(space)$(space)
pad-qms := qms$(space)$(space)$(space)$(space)$(space)$(space)$(space)
pad-rebuild := rebuild$(space)$(space)$(space)
pad-run := run$(space)$(space)$(space)$(space)$(space)$(space)$(space)
pad-state := state$(space)$(space)$(space)$(space)$(space)
pad-test := test$(space)$(space)$(space)$(space)$(space)$(space)
pad10 = $(or $(pad-$1),$1)
show-help = $(let tgt desc,$(subst $(s)##$(s), ,$1),$(let name text,$(patsubst %:,%,$(firstword $(subst $(s),$(space),$(tgt)))) $(strip $(subst $(s),$(space),$(desc))),$(info   $(yellow)$(call pad10,$(name))$(reset) $(text))))

help:
	$(info $(blue)Usage: $(green)gmake [recipe]$(reset))
	$(info $(blue)Pinned Lab5.QMS:$(reset) $(QMS_TAG) ($(QMS_PACKAGE) $(QMS_ENDPOINT)))
	$(info $(blue)QMS_SRC:$(reset) $(QMS_SRC))
	$(info $(blue)Recipes:$(reset))
	$(foreach w,$(sort $(help-words)),$(call show-help,$(w)))
	:
