ifeq ($(filter oneshell,$(.FEATURES)),)
$(error GNU Make ≥ 3.82 required (this is $(MAKE_VERSION) from $(MAKE)). On macOS: brew install make && gmake <target>)
endif

.EXPORT_ALL_VARIABLES:
.ONESHELL:
.SILENT:

SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c
MAKEFLAGS += --no-builtin-rules --no-builtin-variables

# Sibling customization checkout. Override: gmake publish QMS_SRC=/path/to/acu-custom-qms
QMS_SRC ?= $(abspath ../acu-custom-qms)
PIN := customization/Lab5.QMS.pin
CACHE := .cache

pin_val = $(shell awk -F= '/^$(1)=/{print $$2}' $(PIN))
QMS_REPO := $(call pin_val,repo)
QMS_TAG := $(call pin_val,tag)
QMS_ASSET := $(call pin_val,asset)
QMS_SHA256 := $(call pin_val,sha256)
QMS_PACKAGE := $(call pin_val,package)
QMS_ENDPOINT := $(call pin_val,endpoint)
PIN_VERSION := $(patsubst v%,%,$(QMS_TAG))

TENANT := $(shell awk -F= '/^ACU_TENANT=/{print $$2}' .env)

default: help

.PHONY: help preflight rebuild delete create apply run publish fetch qms diff state test

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
	test -e .env || { echo ".env missing"; exit 1; }
	command -v acu >/dev/null \
		|| { echo "acu not on PATH — uv tool install acumatica-cli"; exit 1; }
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

run: ## Lifecycle scenarios (capital → buy → build → sell)
	$(call header,acu run)
	acu run

# Publish the pinned Lab5.QMS zip. Prefers a sibling checkout at the pin tag
# (same .env tenant). This repo never compiles the DLL.
publish: ## Publish pinned Lab5.QMS from QMS_SRC (lab5-qms deploy)
	test -d "$(QMS_SRC)" \
		|| { echo "QMS_SRC missing: $(QMS_SRC) — clone $(QMS_REPO) or pass QMS_SRC="; exit 1; }
	src_version=$$(cd "$(QMS_SRC)" && uv version --short)
	if [[ "$$src_version" != "$(PIN_VERSION)" ]]; then
		echo "QMS_SRC version $$src_version != pin $(PIN_VERSION) ($(PIN))"
		echo "checkout $(QMS_TAG) in $(QMS_SRC) or bump the pin after a Lab5.QMS release"
		exit 1
	fi
	$(call header,lab5-qms deploy $(QMS_TAG) from $(QMS_SRC))
	cd "$(QMS_SRC)" && uv run lab5-qms deploy

fetch: ## Download the pinned GitHub-release zip into .cache/ and verify sha256
	command -v gh >/dev/null \
		|| { echo "gh CLI required — https://cli.github.com/"; exit 1; }
	mkdir -p "$(CACHE)"
	$(call header,Fetching $(QMS_ASSET) $(QMS_TAG))
	gh release download "$(QMS_TAG)" \
		--repo "$(QMS_REPO)" \
		--pattern "$(QMS_ASSET)" \
		--dir "$(CACHE)" \
		--clobber
	got=$$(shasum -a 256 "$(CACHE)/$(QMS_ASSET)" | awk '{print $$1}')
	if [[ "$$got" != "$(QMS_SHA256)" ]]; then
		echo "sha256 mismatch for $(CACHE)/$(QMS_ASSET)"
		echo "  pin  $(QMS_SHA256)"
		echo "  got  $$got"
		exit 1
	fi
	echo "$(CACHE)/$(QMS_ASSET)"

qms: ## Post-publish QMS master (UsrQMS* + Quality Manager; plans PUT still 500)
	$(call header,acu apply config/qms/ item flags + QM users)
	acu apply config/qms/20-stock-item-qms.yaml config/qms/30-qm-role-users.yaml
	$(call header,acu apply config/qms/ inspection plans)
	acu apply config/qms/10-inspection-plans.yaml \
		|| echo "$(yellow)InspectionPlan PUT 500 — seed via SQL or QM.20.10.00 until Lab5.QMS fixes PUT$(reset)"

diff: ## Prove SEED_DIRS have no drift (config/qms/ is post-publish)
	$(call header,acu diff)
	acu diff

state: ## Capture derived-state observations into state/
	$(call header,acu state)
	acu state

rebuild: ## Full CNBN recreate + pinned Lab5.QMS (serial; never acu check)
	$(MAKE) delete
	$(MAKE) create
	$(MAKE) apply
	$(MAKE) run
	$(MAKE) publish
	$(MAKE) qms
	$(MAKE) diff
	$(MAKE) state
	$(call header,rebuild green on $(TENANT))

###############################################################################
# Colors and Headers
###############################################################################

TERM := xterm-256color

blue := $$(tput setaf 4)
green := $$(tput setaf 2)
yellow := $$(tput setaf 3)
reset := $$(tput sgr0)

define header
echo "$(blue)==> $(1) <==$(reset)"
endef

help:
	echo "$(blue)Usage: $(green)gmake [recipe]$(reset)"
	echo "$(blue)Pinned Lab5.QMS:$(reset) $(QMS_TAG) ($(QMS_PACKAGE) $(QMS_ENDPOINT))"
	echo "$(blue)QMS_SRC:$(reset) $(QMS_SRC)"
	echo "$(blue)Recipes:$(reset)"
	awk 'BEGIN {FS = ":.*?## "; sort_cmd = "sort"} /^[a-zA-Z0-9_-]+:.*?## / \
	{ printf "  \033[33m%-10s\033[0m %s\n", $$1, $$2 | sort_cmd; } \
	END {close(sort_cmd)}' $(MAKEFILE_LIST)
