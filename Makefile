# Omics Skills Installer
# Installs agents and skills for Claude Code and Codex CLI.
#
# Layout of an install:
#   ~/.agents/skills/<skill>/     shared skills (links or copies)
#   ~/.agents/omics-skills/       router + generated catalog
#   ~/.claude/agents/<name>.md    Claude agents (links or copies)
#   ~/.codex/agents/<name>.toml   Codex agents (always rendered, never linked)
#   ~/.claude/skills, ~/.codex/skills -> ~/.agents/skills

.PHONY: help install install-claude install-codex install-selected \
        install-skills install-catalog build-catalog prune-removed-skills \
        link-claude-skills link-codex-skills \
        install-hook uninstall-hook hook-status benchmark check-deps \
        uninstall uninstall-selected uninstall-claude uninstall-codex \
        uninstall-skills uninstall-catalog status clean validate test \
        _install-agents _link-skills _uninstall-agents

AGENTS_DIR := $(CURDIR)/agents
SKILLS_DIR := $(CURDIR)/skills
SCRIPTS_DIR := $(CURDIR)/scripts
CATALOG_DIR := $(CURDIR)/catalog
CATALOG_SRC_DIR ?= $(CATALOG_DIR)

AGENT_FILES := omics-scientist.md literature-expert.md science-writer.md dataviz-artist.md
AGENT_COUNT := $(words $(AGENT_FILES))
SKILL_DIRS := $(notdir $(wildcard $(SKILLS_DIR)/*))

CLAUDE_HOME := $(HOME)/.claude
CLAUDE_AGENTS_DIR := $(CLAUDE_HOME)/agents
CLAUDE_SKILLS_DIR := $(CLAUDE_HOME)/skills
CODEX_HOME := $(HOME)/.codex
CODEX_AGENTS_DIR := $(CODEX_HOME)/agents
CODEX_SKILLS_DIR := $(CODEX_HOME)/skills
AGENTS_HOME := $(HOME)/.agents
AGENTS_SKILLS_DIR := $(AGENTS_HOME)/skills
AGENTS_CATALOG_DIR := $(AGENTS_HOME)/omics-skills

# symlink (default) keeps the install tracking this checkout; copy detaches it.
INSTALL_METHOD ?= symlink

# Subsets for scripted installs. Default to everything.
SELECTED_AGENT_FILES ?= $(AGENT_FILES)
SELECTED_SKILL_DIRS ?= $(SKILL_DIRS)

ifeq ($(NO_COLOR),)
  GREEN := \033[0;32m
  YELLOW := \033[0;33m
  BLUE := \033[0;34m
  RED := \033[0;31m
  NC := \033[0m
endif

##@ General

help: ## Display this help
	@echo "$(BLUE)Omics Skills Installer$(NC)"
	@echo ""
	@echo "  make <target> [INSTALL_METHOD=copy] [NO_COLOR=1]"
	@echo ""
	@echo "  Install a subset:"
	@echo "    make install-selected SELECTED_AGENT_FILES=\"omics-scientist.md\" \\"
	@echo "                          SELECTED_SKILL_DIRS=\"bio-logic bio-annotation\""
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-22s$(NC) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Installation

install: check-deps install-claude install-codex ## Install agents and skills for both runtimes
	@echo "$(GREEN)OK Installation complete$(NC)"
	@echo ""
	@$(MAKE) --no-print-directory status

install-claude: build-catalog install-skills install-catalog link-claude-skills ## Install for Claude Code only
	@$(MAKE) --no-print-directory _install-agents \
		AGENT_TARGET_DIR=$(CLAUDE_AGENTS_DIR) AGENT_PLATFORM="Claude Code" AGENT_FORMAT=md
	@echo "$(GREEN)OK Claude Code installation complete$(NC)"

install-codex: build-catalog install-skills install-catalog link-codex-skills ## Install for Codex CLI only
	@$(MAKE) --no-print-directory _install-agents \
		AGENT_TARGET_DIR=$(CODEX_AGENTS_DIR) AGENT_PLATFORM="Codex CLI" AGENT_FORMAT=toml
	@echo "$(GREEN)OK Codex CLI installation complete$(NC)"

# Build a catalog containing only the selected components, install just those,
# and point both runtimes at the result.
install-selected: ## Install only SELECTED_AGENT_FILES / SELECTED_SKILL_DIRS
	@set -e; \
	if [ -n "$(strip $(SELECTED_SKILL_DIRS))" ]; then \
		tmp_catalog=$$(mktemp -d); \
		trap 'rm -rf "$$tmp_catalog"' EXIT; \
		python3 $(SCRIPTS_DIR)/skill_index.py build --repo $(CURDIR) --out "$$tmp_catalog" \
			$(if $(strip $(SELECTED_AGENT_FILES)),$(foreach a,$(SELECTED_AGENT_FILES),--include-agent $(a)),--include-agent __none__) \
			$(foreach s,$(SELECTED_SKILL_DIRS),--include-skill $(s)) >/dev/null; \
		$(MAKE) --no-print-directory install-skills SELECTED_SKILL_DIRS="$(SELECTED_SKILL_DIRS)"; \
		$(MAKE) --no-print-directory install-catalog CATALOG_SRC_DIR="$$tmp_catalog"; \
		$(MAKE) --no-print-directory link-claude-skills link-codex-skills; \
	else \
		echo "$(YELLOW)Skipping shared skills and catalog$(NC)"; \
	fi
	@if [ -n "$(strip $(SELECTED_AGENT_FILES))" ]; then \
		$(MAKE) --no-print-directory _install-agents AGENT_TARGET_DIR=$(CLAUDE_AGENTS_DIR) AGENT_PLATFORM="Claude Code" AGENT_FORMAT=md; \
		$(MAKE) --no-print-directory _install-agents AGENT_TARGET_DIR=$(CODEX_AGENTS_DIR) AGENT_PLATFORM="Codex CLI" AGENT_FORMAT=toml; \
	else \
		echo "$(YELLOW)Skipping agents$(NC)"; \
	fi
	@echo "$(GREEN)OK Installation complete$(NC)"
	@echo ""
	@$(MAKE) --no-print-directory status

build-catalog: ## Build the shared skill catalog files
	@echo "$(BLUE)Building skill catalog...$(NC)"
	@mkdir -p $(CATALOG_DIR)
	@python3 $(SCRIPTS_DIR)/skill_index.py build --repo $(CURDIR) --out $(CATALOG_DIR) >/dev/null
	@echo "  $(GREEN)OK$(NC) $(CATALOG_DIR)/catalog.json"

install-catalog: ## Install the shared skill catalog to ~/.agents/omics-skills
	@echo "$(BLUE)Installing skill catalog to $(AGENTS_CATALOG_DIR)...$(NC)"
	@mkdir -p $(AGENTS_CATALOG_DIR)
	@set -e; for item in skill_index.py README.md catalog.json; do \
		case $$item in \
			skill_index.py) src=$(SCRIPTS_DIR)/$$item ;; \
			catalog.json)   src=$(CATALOG_SRC_DIR)/$$item ;; \
			*)              src=$(CATALOG_DIR)/$$item ;; \
		esac; \
		target="$(AGENTS_CATALOG_DIR)/$$item"; \
		rm -rf "$$target"; \
		if [ "$(INSTALL_METHOD)" = "symlink" ] && { [ "$$item" != "catalog.json" ] || [ "$(CATALOG_SRC_DIR)" = "$(CATALOG_DIR)" ]; }; then \
			ln -sf "$$src" "$$target"; \
		else \
			cp "$$src" "$$target"; \
		fi; \
		echo "  $(GREEN)OK$(NC) $$item"; \
	done

# One agent installer for both runtimes. Claude reads the Markdown source, so it
# can be linked; Codex needs generated TOML, so it is always rendered afresh and
# must be re-run after editing an agent prompt.
_install-agents:
	@echo "$(BLUE)Installing agents to $(AGENT_PLATFORM)...$(NC)"
	@mkdir -p $(AGENT_TARGET_DIR)
	@set -e; for agent in $(SELECTED_AGENT_FILES); do \
		source="$(AGENTS_DIR)/$$agent"; \
		name=$${agent%.md}; \
		target="$(AGENT_TARGET_DIR)/$$name.$(AGENT_FORMAT)"; \
		[ -f "$$source" ] || { echo "  $(RED)ERROR$(NC) $$agent not found"; exit 1; }; \
		if [ -L "$$target" ]; then \
			rm "$$target"; \
		elif [ -f "$$target" ]; then \
			mv "$$target" "$$target.bak.$$(date +%s%N)"; \
			echo "  $(YELLOW)Backed up existing $$name.$(AGENT_FORMAT)$(NC)"; \
		fi; \
		if [ "$(AGENT_FORMAT)" = "toml" ]; then \
			legacy="$(AGENT_TARGET_DIR)/$$name.md"; \
			if [ -e "$$legacy" ]; then mv "$$legacy" "$$legacy.legacy.bak.$$(date +%s%N)"; fi; \
			python3 $(SCRIPTS_DIR)/render_codex_agent.py "$$source" "$$target"; \
		elif [ "$(INSTALL_METHOD)" = "symlink" ]; then \
			ln -sf "$$source" "$$target"; \
		else \
			cp "$$source" "$$target"; \
		fi; \
		echo "  $(GREEN)OK$(NC) $$name.$(AGENT_FORMAT)"; \
	done

prune-removed-skills: ## Retire skills present in the installed catalog but absent from this checkout
	@python3 $(SCRIPTS_DIR)/prune_removed_skills.py \
		--skills-dir $(SKILLS_DIR) \
		--installed-catalog $(AGENTS_CATALOG_DIR)/catalog.json \
		--installed-skills-dir $(AGENTS_SKILLS_DIR) \
		--backup-dir $(AGENTS_CATALOG_DIR)/retired-skills

# Replaced entries are archived under ~/.agents/omics-skills/previous-skills so a
# stale copy never stays discoverable as a skill. `make clean` clears that archive.
install-skills: prune-removed-skills ## Install skills to ~/.agents/skills
	@echo "$(BLUE)Installing skills to $(AGENTS_SKILLS_DIR)...$(NC)"
	@mkdir -p $(AGENTS_SKILLS_DIR)
	@set -e; for name in $(SELECTED_SKILL_DIRS); do \
		[ -d "$(SKILLS_DIR)/$$name" ] || { echo "  $(RED)ERROR$(NC) $$name not found"; exit 1; }; \
	done; \
	for name in $(SELECTED_SKILL_DIRS); do \
		target="$(AGENTS_SKILLS_DIR)/$$name"; \
		if [ -L "$$target" ]; then \
			rm "$$target"; \
		elif [ -e "$$target" ]; then \
			archive="$(AGENTS_CATALOG_DIR)/previous-skills"; \
			mkdir -p "$$archive"; \
			mv "$$target" "$$archive/$$name.$$(date +%s%N)"; \
		fi; \
		if [ "$(INSTALL_METHOD)" = "symlink" ]; then \
			ln -sfn "$(SKILLS_DIR)/$$name" "$$target"; \
		else \
			cp -r "$(SKILLS_DIR)/$$name" "$$target"; \
		fi; \
	done; \
	echo "  $(GREEN)OK$(NC) $(words $(SELECTED_SKILL_DIRS)) skills"

link-claude-skills: ## Link ~/.claude/skills to ~/.agents/skills
	@$(MAKE) --no-print-directory _link-skills LINK_TARGET=$(CLAUDE_SKILLS_DIR) LINK_HOME=$(CLAUDE_HOME)

link-codex-skills: ## Link ~/.codex/skills to ~/.agents/skills
	@$(MAKE) --no-print-directory _link-skills LINK_TARGET=$(CODEX_SKILLS_DIR) LINK_HOME=$(CODEX_HOME)

# A real directory there belongs to the user, not to us: replacing it with a
# symlink would hide every skill inside, so stop and let them move it.
_link-skills:
	@mkdir -p $(LINK_HOME)
	@if [ -e $(LINK_TARGET) ] && [ ! -L $(LINK_TARGET) ]; then \
		echo "  $(RED)ERROR$(NC) $(LINK_TARGET) is a real directory holding your own skills."; \
		echo "         Move or merge it into $(AGENTS_SKILLS_DIR), then re-run."; \
		exit 1; \
	fi
	@ln -sfn $(AGENTS_SKILLS_DIR) $(LINK_TARGET)
	@echo "  $(GREEN)OK$(NC) $(LINK_TARGET) -> $(AGENTS_SKILLS_DIR)"

##@ Hook and benchmark

install-hook: ## Install the routing-hint hook for Claude Code + Codex CLI
	@python3 $(SCRIPTS_DIR)/install_hook.py install

uninstall-hook: ## Remove the routing-hint hook from Claude Code + Codex CLI
	@python3 $(SCRIPTS_DIR)/install_hook.py uninstall

hook-status: ## Show whether the routing-hint hook is installed per runtime
	@python3 $(SCRIPTS_DIR)/install_hook.py status

benchmark: ## Run the routing benchmark and diff against docs/routing_baseline.json
	@python3 $(SCRIPTS_DIR)/routing_benchmark.py --compare docs/routing_baseline.json

##@ Uninstallation

uninstall: uninstall-hook uninstall-claude uninstall-codex uninstall-skills uninstall-catalog ## Uninstall everything
	@echo "$(GREEN)OK Uninstallation complete$(NC)"

uninstall-selected: ## Uninstall only SELECTED_AGENT_FILES / SELECTED_SKILL_DIRS
	@for agent in $(SELECTED_AGENT_FILES); do \
		name=$${agent%.md}; \
		rm -f "$(CLAUDE_AGENTS_DIR)/$$name.md" "$(CODEX_AGENTS_DIR)/$$name.toml" "$(CODEX_AGENTS_DIR)/$$name.md"; \
	done
	@for name in $(SELECTED_SKILL_DIRS); do rm -rf "$(AGENTS_SKILLS_DIR)/$$name"; done
	@echo "$(GREEN)OK Removed the selected components$(NC)"
	@$(MAKE) --no-print-directory status

uninstall-claude: ## Uninstall from Claude Code
	@$(MAKE) --no-print-directory _uninstall-agents \
		AGENT_TARGET_DIR=$(CLAUDE_AGENTS_DIR) AGENT_PLATFORM="Claude Code" AGENT_FORMAT=md \
		LINK_TARGET=$(CLAUDE_SKILLS_DIR)

uninstall-codex: ## Uninstall from Codex CLI
	@$(MAKE) --no-print-directory _uninstall-agents \
		AGENT_TARGET_DIR=$(CODEX_AGENTS_DIR) AGENT_PLATFORM="Codex CLI" AGENT_FORMAT=toml \
		LINK_TARGET=$(CODEX_SKILLS_DIR)

# Removes only our own agents and a skills symlink that points at our tree.
_uninstall-agents:
	@echo "$(BLUE)Uninstalling from $(AGENT_PLATFORM)...$(NC)"
	@removed=0; \
	for agent in $(AGENT_FILES); do \
		name=$${agent%.md}; \
		for target in "$(AGENT_TARGET_DIR)/$$name.$(AGENT_FORMAT)" "$(AGENT_TARGET_DIR)/$$name.md"; do \
			if [ -L "$$target" ] || [ -f "$$target" ]; then rm -f "$$target"; removed=$$((removed + 1)); fi; \
		done; \
	done; \
	echo "  $(GREEN)OK$(NC) removed $$removed agent file(s)"
	@if [ -L "$(LINK_TARGET)" ]; then \
		if [ "$$(readlink $(LINK_TARGET))" = "$(AGENTS_SKILLS_DIR)" ]; then \
			rm "$(LINK_TARGET)"; \
			echo "  $(GREEN)OK$(NC) removed $(LINK_TARGET)"; \
		else \
			echo "  $(YELLOW)INFO$(NC) left $(LINK_TARGET) alone (points elsewhere)"; \
		fi; \
	fi

uninstall-skills: ## Remove omics-skills from ~/.agents/skills
	@echo "$(BLUE)Uninstalling skills from $(AGENTS_SKILLS_DIR)...$(NC)"
	@removed=0; \
	for name in $(SKILL_DIRS); do \
		target="$(AGENTS_SKILLS_DIR)/$$name"; \
		if [ -L "$$target" ] || [ -d "$$target" ]; then rm -rf "$$target"; removed=$$((removed + 1)); fi; \
	done; \
	echo "  $(GREEN)OK$(NC) removed $$removed/$(words $(SKILL_DIRS)) skills"

uninstall-catalog: ## Remove the shared skill catalog from ~/.agents/omics-skills
	@if [ -d $(AGENTS_CATALOG_DIR) ]; then \
		rm -rf $(AGENTS_CATALOG_DIR); \
		echo "  $(GREEN)OK$(NC) removed $(AGENTS_CATALOG_DIR)"; \
	else \
		echo "  $(YELLOW)INFO$(NC) nothing to remove"; \
	fi

##@ Status and maintenance

check-deps: ## Check if required commands are available
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v claude >/dev/null 2>&1 && echo "  $(GREEN)OK$(NC) Claude Code CLI found" || echo "  $(YELLOW)INFO$(NC) Claude Code CLI not found"
	@command -v codex  >/dev/null 2>&1 && echo "  $(GREEN)OK$(NC) Codex CLI found"       || echo "  $(YELLOW)INFO$(NC) Codex CLI not found"
	@python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null \
		&& echo "  $(GREEN)OK$(NC) Python $$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))') found" \
		|| echo "  $(YELLOW)INFO$(NC) Python 3.11+ not found (Codex agent rendering needs tomllib)"
	@command -v uv >/dev/null 2>&1 && echo "  $(GREEN)OK$(NC) uv found" || echo "  $(YELLOW)INFO$(NC) uv not found (needed for tests and skill helpers)"

status: ## Show installation status
	@echo "$(BLUE)Installation Status$(NC)"
	@printf "  skills   $(AGENTS_SKILLS_DIR): "; \
	installed=0; for name in $(SKILL_DIRS); do \
		[ -e "$(AGENTS_SKILLS_DIR)/$$name" ] && installed=$$((installed + 1)) || true; done; \
	echo "$$installed/$(words $(SKILL_DIRS))"
	@printf "  catalog  $(AGENTS_CATALOG_DIR): "; \
	installed=0; for item in skill_index.py README.md catalog.json; do \
		[ -e "$(AGENTS_CATALOG_DIR)/$$item" ] && installed=$$((installed + 1)) || true; done; \
	echo "$$installed/3"
	@printf "  Claude   $(CLAUDE_AGENTS_DIR): "; \
	installed=0; for agent in $(AGENT_FILES); do \
		[ -e "$(CLAUDE_AGENTS_DIR)/$$agent" ] && installed=$$((installed + 1)) || true; done; \
	echo "$$installed/$(AGENT_COUNT) agents"
	@printf "  Codex    $(CODEX_AGENTS_DIR): "; \
	installed=0; for agent in $(AGENT_FILES); do \
		[ -e "$(CODEX_AGENTS_DIR)/$${agent%.md}.toml" ] && installed=$$((installed + 1)) || true; done; \
	echo "$$installed/$(AGENT_COUNT) agents"
	@for link in $(CLAUDE_SKILLS_DIR) $(CODEX_SKILLS_DIR); do \
		if [ -L "$$link" ]; then echo "  link     $$link -> $$(readlink $$link)"; \
		elif [ -e "$$link" ]; then echo "  $(YELLOW)link     $$link is not a symlink$(NC)"; \
		else echo "  link     $$link: absent"; fi; \
	done

validate: ## Validate installation
	@echo "$(BLUE)Validating installation...$(NC)"
	@if ! [ -d $(CLAUDE_AGENTS_DIR) ] && ! [ -d $(CODEX_AGENTS_DIR) ]; then \
		echo "  $(RED)ERROR$(NC) neither $(CLAUDE_AGENTS_DIR) nor $(CODEX_AGENTS_DIR) exists; nothing is installed"; \
		exit 1; \
	fi
	@errors=0; \
	for agent in $(AGENT_FILES); do \
		name=$${agent%.md}; \
		if [ -d $(CLAUDE_AGENTS_DIR) ] && ! [ -e "$(CLAUDE_AGENTS_DIR)/$$agent" ]; then \
			echo "  $(RED)ERROR$(NC) missing $$agent in Claude Code"; errors=$$((errors + 1)); fi; \
		if [ -d $(CODEX_AGENTS_DIR) ] && ! [ -e "$(CODEX_AGENTS_DIR)/$$name.toml" ]; then \
			echo "  $(RED)ERROR$(NC) missing $$name.toml in Codex CLI"; errors=$$((errors + 1)); fi; \
	done; \
	for name in $(SKILL_DIRS); do \
		if ! [ -e "$(AGENTS_SKILLS_DIR)/$$name" ]; then \
			echo "  $(RED)ERROR$(NC) missing $$name in shared skills"; errors=$$((errors + 1)); fi; \
	done; \
	if [ $$errors -eq 0 ]; then echo "  $(GREEN)OK$(NC) installation valid"; \
	else echo "  $(RED)ERROR$(NC) found $$errors problem(s)"; exit 1; fi

clean: ## Remove agent backups and the previous-skills / retired-skills archives
	@for agent in $(AGENT_FILES); do \
		name=$${agent%.md}; \
		rm -f $(CLAUDE_AGENTS_DIR)/$$agent.bak* \
			$(CODEX_AGENTS_DIR)/$$name.toml.bak* \
			$(CODEX_AGENTS_DIR)/$$name.md.legacy.bak* 2>/dev/null || true; \
	done
	@rm -rf $(AGENTS_CATALOG_DIR)/previous-skills $(AGENTS_CATALOG_DIR)/retired-skills 2>/dev/null || true
	@echo "$(GREEN)OK Removed agent backups and the previous-skills and retired-skills archives$(NC)"

##@ Testing

test: ## Run the repository gates
	@uv run --script $(SCRIPTS_DIR)/validate-skills.py
	@python3 $(SCRIPTS_DIR)/validate-supplementary-docs.py
	@python3 $(SCRIPTS_DIR)/validate-citations.py
	@uv run --no-project --with pytest --with requests --with PyYAML python -m pytest tests -q
	@$(MAKE) --no-print-directory benchmark
