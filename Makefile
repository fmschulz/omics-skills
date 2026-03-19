# Omics Skills Installer
# Installs agents and skills for Claude Code and Codex CLI

.PHONY: help install install-claude install-codex install-agents install-skills \
        install-claude-skills install-codex-skills link-claude-skills link-codex-skills \
        install-codex-tools build-catalog install-catalog uninstall uninstall-claude \
        uninstall-codex uninstall-skills uninstall-catalog status check-deps clean test

# Directories
AGENTS_DIR := $(CURDIR)/agents
SKILLS_DIR := $(CURDIR)/skills
SCRIPTS_DIR := $(CURDIR)/scripts
CATALOG_DIR := $(CURDIR)/catalog

# Specific agent files (flattened in agents/ directory)
AGENT_FILES := omics-scientist.md literature-expert.md science-writer.md dataviz-artist.md codexloop.md
AGENT_COUNT := $(words $(AGENT_FILES))

# Installation targets
CLAUDE_HOME := $(HOME)/.claude
CLAUDE_AGENTS_DIR := $(CLAUDE_HOME)/agents
CLAUDE_SKILLS_DIR := $(CLAUDE_HOME)/skills

AGENTS_HOME := $(HOME)/.agents
AGENTS_SKILLS_DIR := $(AGENTS_HOME)/skills
AGENTS_CATALOG_DIR := $(AGENTS_HOME)/omics-skills

CODEX_HOME := $(HOME)/.codex
CODEX_AGENTS_DIR := $(CODEX_HOME)/agents
CODEX_SKILLS_DIR := $(CODEX_HOME)/skills
CODEX_BIN_DIR := $(CODEX_HOME)/bin
CODEXLOOP_LAUNCHER := $(CODEX_BIN_DIR)/codexloop

# Installation method (symlink or copy)
# Use INSTALL_METHOD=copy for copying instead of symlinking
INSTALL_METHOD ?= symlink

# Verbosity control
# Use VERBOSE=1 to show each file being installed/uninstalled
# Default is compact progress display
VERBOSE ?= 0

# Colors for output (disabled if NO_COLOR is set or not a TTY)
ifeq ($(NO_COLOR),)
  ifeq ($(shell test -t 1 && echo 1),1)
    GREEN := \033[0;32m
    YELLOW := \033[0;33m
    BLUE := \033[0;34m
    RED := \033[0;31m
    NC := \033[0m
  else
    GREEN :=
    YELLOW :=
    BLUE :=
    RED :=
    NC :=
  endif
else
  GREEN :=
  YELLOW :=
  BLUE :=
  RED :=
  NC :=
endif

##@ General

help: ## Display this help
	@echo "$(BLUE)Omics Skills Installer$(NC)"
	@echo ""
	@echo "Usage:"
	@echo "  make <target> [OPTIONS]"
	@echo ""
	@echo "Options:"
	@echo "  INSTALL_METHOD=copy    Copy files instead of creating symlinks"
	@echo "  VERBOSE=1              Show each file being installed/uninstalled"
	@echo "  NO_COLOR=1             Disable colored output"
	@echo ""
	@echo "Examples:"
	@echo "  make install                      # Install with default settings"
	@echo "  make install VERBOSE=1            # Show detailed progress"
	@echo "  make install INSTALL_METHOD=copy  # Copy files instead of symlinks"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Installation

install: check-deps install-claude install-codex ## Install for both Claude Code and Codex
	@echo "$(GREEN)✓ Installation complete!$(NC)"
	@echo ""
	@$(MAKE) --no-print-directory status

install-claude: build-catalog install-skills install-catalog install-claude-agents link-claude-skills ## Install for Claude Code only
	@echo "$(GREEN)✓ Claude Code installation complete$(NC)"

install-codex: build-catalog install-skills install-catalog install-codex-agents link-codex-skills install-codex-tools ## Install for Codex CLI only
	@echo "$(GREEN)✓ Codex CLI installation complete$(NC)"
	@echo "  Skills linked at $(CODEX_SKILLS_DIR)"
	@echo "  CodexLoop launcher: $(CODEXLOOP_LAUNCHER)"

build-catalog: ## Build the shared skill catalog files
	@echo "$(BLUE)Building skill catalog...$(NC)"
	@mkdir -p $(CATALOG_DIR)
	@python3 $(SCRIPTS_DIR)/skill_index.py build --repo $(CURDIR) --out $(CATALOG_DIR) >/dev/null
	@echo "  $(GREEN)✓$(NC) $(CATALOG_DIR)/catalog.json"
	@echo "  $(GREEN)✓$(NC) $(CATALOG_DIR)/relationships.json"
	@echo "  $(GREEN)✓$(NC) $(CATALOG_DIR)/routing.json"

install-catalog: ## Install the shared skill catalog to ~/.agents/omics-skills
	@echo "$(BLUE)Installing skill catalog to $(AGENTS_CATALOG_DIR)...$(NC)"
	@mkdir -p $(AGENTS_CATALOG_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@for item in skill_index.py README.md catalog.json relationships.json routing.json; do \
		if [ "$$item" = "skill_index.py" ]; then \
			src=$(SCRIPTS_DIR)/$$item; \
		else \
			src=$(CATALOG_DIR)/$$item; \
		fi; \
		target=$(AGENTS_CATALOG_DIR)/$$item; \
		if [ -L $$target ]; then \
			rm $$target; \
		elif [ -e $$target ]; then \
			rm -rf $$target; \
		fi; \
		ln -sf $$src $$target; \
		echo "  $(GREEN)✓$(NC) $$item"; \
	done
else
	@for item in skill_index.py README.md catalog.json relationships.json routing.json; do \
		if [ "$$item" = "skill_index.py" ]; then \
			src=$(SCRIPTS_DIR)/$$item; \
		else \
			src=$(CATALOG_DIR)/$$item; \
		fi; \
		target=$(AGENTS_CATALOG_DIR)/$$item; \
		if [ -e $$target ]; then \
			rm -rf $$target; \
		fi; \
		cp $$src $$target; \
		echo "  $(GREEN)✓$(NC) $$item"; \
	done
endif

install-claude-agents: ## Install agents to Claude Code
	@echo "$(BLUE)Installing agents to Claude Code...$(NC)"
	@mkdir -p $(CLAUDE_AGENTS_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		basename=$$(basename $$agent); \
		target=$(CLAUDE_AGENTS_DIR)/$$basename; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -L $$target ]; then \
			echo "  Updating symlink: $$basename"; \
			rm $$target; \
		elif [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$basename exists (backing up)$(NC)"; \
			mv $$target $$target.bak; \
		fi; \
		ln -sf $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$basename"; \
	done
else
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		basename=$$(basename $$agent); \
		target=$(CLAUDE_AGENTS_DIR)/$$basename; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$basename exists (backing up)$(NC)"; \
			cp $$target $$target.bak; \
		fi; \
		cp $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$basename"; \
	done
endif

install-skills: ## Install skills to ~/.agents/skills
	@echo "$(BLUE)Installing skills to $(AGENTS_SKILLS_DIR)...$(NC)"
	@mkdir -p $(AGENTS_SKILLS_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d | wc -l); \
	current=0; \
	for skill in $(SKILLS_DIR)/*; do \
		if [ -d $$skill ]; then \
			current=$$((current + 1)); \
			basename=$$(basename $$skill); \
			target=$(AGENTS_SKILLS_DIR)/$$basename; \
			if [ -L $$target ]; then \
				rm $$target; \
			elif [ -d $$target ]; then \
				mv $$target $$target.bak; \
			fi; \
			ln -sf $$skill $$target; \
			if [ "$(VERBOSE)" = "1" ]; then \
				echo "  [$$current/$$total] $(GREEN)✓$(NC) $$basename"; \
			else \
				printf "\r  Progress: $$current/$$total skills"; \
			fi; \
		fi; \
	done; \
	if [ "$(VERBOSE)" != "1" ]; then \
		printf "\r  $(GREEN)✓$(NC) Installed: $$total/$$total skills\n"; \
	else \
		echo "  $(GREEN)✓$(NC) Completed: $$total/$$total skills"; \
	fi
else
	@total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d | wc -l); \
	current=0; \
	for skill in $(SKILLS_DIR)/*; do \
		if [ -d $$skill ]; then \
			current=$$((current + 1)); \
			basename=$$(basename $$skill); \
			target=$(AGENTS_SKILLS_DIR)/$$basename; \
			if [ -d $$target ]; then \
				mv $$target $$target.bak; \
			fi; \
			cp -r $$skill $$target; \
			if [ "$(VERBOSE)" = "1" ]; then \
				echo "  [$$current/$$total] $(GREEN)✓$(NC) $$basename"; \
			else \
				printf "\r  Progress: $$current/$$total skills"; \
			fi; \
		fi; \
	done; \
	if [ "$(VERBOSE)" != "1" ]; then \
		printf "\r  $(GREEN)✓$(NC) Installed: $$total/$$total skills\n"; \
	else \
		echo "  $(GREEN)✓$(NC) Completed: $$total/$$total skills"; \
	fi
endif

install-claude-skills: install-skills link-claude-skills ## Backwards-compatible target

link-claude-skills: ## Link Claude skills dir to ~/.agents/skills
	@echo "$(BLUE)Linking Claude skills to $(AGENTS_SKILLS_DIR)...$(NC)"
	@mkdir -p $(CLAUDE_HOME)
	@if [ -L $(CLAUDE_SKILLS_DIR) ]; then \
		ln -sfn $(AGENTS_SKILLS_DIR) $(CLAUDE_SKILLS_DIR); \
	elif [ -e $(CLAUDE_SKILLS_DIR) ]; then \
		backup=$(CLAUDE_SKILLS_DIR).bak; \
		if [ -e $$backup ]; then \
			backup=$(CLAUDE_SKILLS_DIR).bak.$$(date +%s); \
		fi; \
		mv $(CLAUDE_SKILLS_DIR) $$backup; \
		ln -sfn $(AGENTS_SKILLS_DIR) $(CLAUDE_SKILLS_DIR); \
		echo "  $(YELLOW)Backed up existing skills to $$backup$(NC)"; \
	else \
		ln -sfn $(AGENTS_SKILLS_DIR) $(CLAUDE_SKILLS_DIR); \
	fi
	@echo "  $(GREEN)✓$(NC) $(CLAUDE_SKILLS_DIR) -> $(AGENTS_SKILLS_DIR)"

link-codex-skills: ## Link Codex skills dir to ~/.agents/skills
	@echo "$(BLUE)Linking Codex skills to $(AGENTS_SKILLS_DIR)...$(NC)"
	@mkdir -p $(CODEX_HOME)
	@if [ -L $(CODEX_SKILLS_DIR) ]; then \
		ln -sfn $(AGENTS_SKILLS_DIR) $(CODEX_SKILLS_DIR); \
	elif [ -e $(CODEX_SKILLS_DIR) ]; then \
		backup=$(CODEX_SKILLS_DIR).bak; \
		if [ -e $$backup ]; then \
			backup=$(CODEX_SKILLS_DIR).bak.$$(date +%s); \
		fi; \
		mv $(CODEX_SKILLS_DIR) $$backup; \
		ln -sfn $(AGENTS_SKILLS_DIR) $(CODEX_SKILLS_DIR); \
		echo "  $(YELLOW)Backed up existing Codex skills to $$backup$(NC)"; \
	else \
		ln -sfn $(AGENTS_SKILLS_DIR) $(CODEX_SKILLS_DIR); \
	fi
	@echo "  $(GREEN)✓$(NC) $(CODEX_SKILLS_DIR) -> $(AGENTS_SKILLS_DIR)"

install-codex-tools: ## Install codexloop launcher to ~/.codex/bin
	@echo "$(BLUE)Installing CodexLoop launcher...$(NC)"
	@mkdir -p $(CODEX_BIN_DIR)
	@printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' 'export PYTHONPATH="$$HOME/.codex/skills$${PYTHONPATH:+:$$PYTHONPATH}"' 'exec python3 -m codexloop "$$@"' > $(CODEXLOOP_LAUNCHER)
	@chmod +x $(CODEXLOOP_LAUNCHER)
	@echo "  $(GREEN)✓$(NC) $(CODEXLOOP_LAUNCHER)"
	@if echo ":$$PATH:" | grep -q ":$(CODEX_BIN_DIR):"; then \
		echo "  $(GREEN)✓$(NC) $(CODEX_BIN_DIR) is on PATH"; \
	else \
		echo "  $(YELLOW)Note: add $(CODEX_BIN_DIR) to PATH or call $(CODEXLOOP_LAUNCHER) directly$(NC)"; \
	fi

install-codex-agents: ## Install agents to Codex CLI
	@echo "$(BLUE)Installing agents to Codex CLI...$(NC)"
	@mkdir -p $(CODEX_AGENTS_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		basename=$$(basename $$agent); \
		target=$(CODEX_AGENTS_DIR)/$$basename; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -L $$target ]; then \
			echo "  Updating symlink: $$basename"; \
			rm $$target; \
		elif [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$basename exists (backing up)$(NC)"; \
			mv $$target $$target.bak; \
		fi; \
		ln -sf $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$basename"; \
	done
else
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		basename=$$(basename $$agent); \
		target=$(CODEX_AGENTS_DIR)/$$basename; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$basename exists (backing up)$(NC)"; \
			cp $$target $$target.bak; \
		fi; \
		cp $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$basename"; \
	done
endif

install-codex-skills: ## Backwards-compatible target
	@$(MAKE) --no-print-directory link-codex-skills

##@ Dependencies

check-deps: ## Check if required commands are available
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v claude >/dev/null 2>&1 && echo "  $(GREEN)✓$(NC) Claude Code CLI found" || echo "  $(YELLOW)○$(NC) Claude Code CLI not found (install from https://claude.com/claude-code)"
	@command -v codex >/dev/null 2>&1 && echo "  $(GREEN)✓$(NC) Codex CLI found" || echo "  $(YELLOW)○$(NC) Codex CLI not found (optional)"
	@command -v python3 >/dev/null 2>&1 && echo "  $(GREEN)✓$(NC) Python 3 found" || echo "  $(YELLOW)○$(NC) Python 3 not found (required for installation and some skills)"
	@echo ""

install-python-deps: ## Install Python dependencies for skills
	@echo "$(BLUE)Installing Python dependencies for skills...$(NC)"
	@if command -v pip3 >/dev/null 2>&1; then \
		for req in $(SKILLS_DIR)/*/requirements.txt; do \
			if [ -f $$req ]; then \
				skill=$$(dirname $$req); \
				basename=$$(basename $$skill); \
				echo "  Installing deps for $$basename..."; \
				pip3 install -r $$req --quiet; \
				echo "  $(GREEN)✓$(NC) $$basename"; \
			fi; \
		done; \
	else \
		echo "  $(RED)✗$(NC) pip3 not found - cannot install Python dependencies"; \
		exit 1; \
	fi

##@ Uninstallation

uninstall: uninstall-claude uninstall-codex uninstall-skills uninstall-catalog ## Uninstall from both platforms
	@echo "$(GREEN)✓ Uninstallation complete$(NC)"

uninstall-claude: ## Uninstall from Claude Code
	@echo "$(BLUE)Uninstalling from Claude Code...$(NC)"
	@current=0; \
	for agent in $(AGENT_FILES); do \
		basename=$$(basename $$agent); \
		target=$(CLAUDE_AGENTS_DIR)/$$basename; \
		if [ -L $$target ] || [ -f $$target ]; then \
			current=$$((current + 1)); \
			rm $$target; \
			if [ "$(VERBOSE)" = "1" ]; then \
				echo "  [$$current/$(AGENT_COUNT)] $(GREEN)✓$(NC) Removed $$basename"; \
			else \
				printf "\r  Agents: $$current/$(AGENT_COUNT)"; \
			fi; \
		fi; \
	done; \
	if [ "$(VERBOSE)" != "1" ]; then \
		printf "\r  $(GREEN)✓$(NC) Removed: $$current/$(AGENT_COUNT) agents\n"; \
	else \
		echo "  $(GREEN)✓$(NC) Completed: $$current/$(AGENT_COUNT) agents"; \
	fi
	@echo "$(GREEN)✓ Claude Code uninstalled$(NC)"

uninstall-codex: ## Uninstall from Codex CLI
	@echo "$(BLUE)Uninstalling from Codex CLI...$(NC)"
	@current=0; \
	for agent in $(AGENT_FILES); do \
		basename=$$(basename $$agent); \
		target=$(CODEX_AGENTS_DIR)/$$basename; \
		if [ -L $$target ] || [ -f $$target ]; then \
			current=$$((current + 1)); \
			rm $$target; \
			if [ "$(VERBOSE)" = "1" ]; then \
				echo "  [$$current/$(AGENT_COUNT)] $(GREEN)✓$(NC) Removed $$basename"; \
			else \
				printf "\r  Agents: $$current/$(AGENT_COUNT)"; \
			fi; \
		fi; \
	done; \
	if [ "$(VERBOSE)" != "1" ]; then \
		printf "\r  $(GREEN)✓$(NC) Removed: $$current/$(AGENT_COUNT) agents\n"; \
	else \
		echo "  $(GREEN)✓$(NC) Completed: $$current/$(AGENT_COUNT) agents"; \
	fi
	@if [ -f $(CODEXLOOP_LAUNCHER) ] || [ -L $(CODEXLOOP_LAUNCHER) ]; then \
		rm $(CODEXLOOP_LAUNCHER); \
		echo "  $(GREEN)✓$(NC) Removed $(CODEXLOOP_LAUNCHER)"; \
	fi
	@if [ -L $(CODEX_SKILLS_DIR) ]; then \
		rm $(CODEX_SKILLS_DIR); \
		echo "  $(GREEN)✓$(NC) Removed $(CODEX_SKILLS_DIR) symlink"; \
	fi
	@echo "$(GREEN)✓ Codex CLI uninstalled$(NC)"

uninstall-skills: ## Remove omics-skills from ~/.agents/skills
	@echo "$(BLUE)Uninstalling skills from $(AGENTS_SKILLS_DIR)...$(NC)"
	@total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d | wc -l); \
	current=0; \
	for skill in $(SKILLS_DIR)/*; do \
		if [ -d $$skill ]; then \
			basename=$$(basename $$skill); \
			target=$(AGENTS_SKILLS_DIR)/$$basename; \
			if [ -L $$target ] || [ -d $$target ]; then \
				current=$$((current + 1)); \
				rm -rf $$target; \
				if [ "$(VERBOSE)" = "1" ]; then \
					echo "  [$$current/$$total] $(GREEN)✓$(NC) Removed $$basename"; \
				else \
					printf "\r  Skills: $$current/$$total"; \
				fi; \
			fi; \
		fi; \
	done; \
	if [ "$(VERBOSE)" != "1" ]; then \
		printf "\r  $(GREEN)✓$(NC) Removed: $$current/$$total skills\n"; \
	else \
		echo "  $(GREEN)✓$(NC) Completed: $$current/$$total skills"; \
	fi

uninstall-catalog: ## Remove the shared skill catalog from ~/.agents/omics-skills
	@echo "$(BLUE)Uninstalling skill catalog from $(AGENTS_CATALOG_DIR)...$(NC)"
	@if [ -d $(AGENTS_CATALOG_DIR) ]; then \
		rm -rf $(AGENTS_CATALOG_DIR); \
		echo "  $(GREEN)✓$(NC) Removed $(AGENTS_CATALOG_DIR)"; \
	else \
		echo "  $(YELLOW)○$(NC) Nothing to remove"; \
	fi

##@ Status

status: ## Show installation status
	@echo "$(BLUE)Installation Status$(NC)"
	@echo ""
	@echo "$(YELLOW)Shared Skills:$(NC)"
	@echo "  Skills directory: $(AGENTS_SKILLS_DIR)"
	@if [ -d $(AGENTS_SKILLS_DIR) ]; then \
		total=$$(find -L $(AGENTS_SKILLS_DIR) -mindepth 1 -maxdepth 1 \( -type d -o -type l \) 2>/dev/null | wc -l); \
		installed=0; \
		skills_total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l); \
		for skill in $(SKILLS_DIR)/*; do \
			if [ -d $$skill ]; then \
				basename=$$(basename $$skill); \
				if [ -d $(AGENTS_SKILLS_DIR)/$$basename ] || [ -L $(AGENTS_SKILLS_DIR)/$$basename ]; then \
					installed=$$((installed + 1)); \
				fi; \
			fi; \
		done; \
		echo "  Omics-skills skills: $$installed/$$skills_total installed ($$total total in directory)"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "  Catalog directory: $(AGENTS_CATALOG_DIR)"
	@if [ -d $(AGENTS_CATALOG_DIR) ]; then \
		installed=0; \
		for item in skill_index.py README.md catalog.json relationships.json routing.json; do \
			if [ -f $(AGENTS_CATALOG_DIR)/$$item ] || [ -L $(AGENTS_CATALOG_DIR)/$$item ]; then \
				installed=$$((installed + 1)); \
			fi; \
		done; \
		echo "  Skill catalog files: $$installed/5 installed"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Claude Code:$(NC)"
	@echo "  Agents directory: $(CLAUDE_AGENTS_DIR)"
	@if [ -d $(CLAUDE_AGENTS_DIR) ]; then \
		total=$$(ls -1 $(CLAUDE_AGENTS_DIR)/*.md 2>/dev/null | wc -l); \
		installed=0; \
		skills_total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l); \
		for agent in $(AGENT_FILES); do \
			basename=$$(basename $$agent); \
			if [ -f $(CLAUDE_AGENTS_DIR)/$$basename ] || [ -L $(CLAUDE_AGENTS_DIR)/$$basename ]; then \
				installed=$$((installed + 1)); \
			fi; \
		done; \
		echo "  Omics-skills agents: $$installed/$(AGENT_COUNT) installed ($$total total in directory)"; \
		for agent in $(AGENT_FILES); do \
			basename=$$(basename $$agent); \
			if [ -f $(CLAUDE_AGENTS_DIR)/$$basename ] || [ -L $(CLAUDE_AGENTS_DIR)/$$basename ]; then \
				if [ -L $(CLAUDE_AGENTS_DIR)/$$basename ]; then \
					echo "    $(GREEN)✓$(NC) $$basename (symlink)"; \
				else \
					echo "    $(GREEN)✓$(NC) $$basename (copy)"; \
				fi; \
			else \
				echo "    $(RED)✗$(NC) $$basename"; \
			fi; \
		done; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "  Skills directory: $(CLAUDE_SKILLS_DIR)"
	@if [ -L $(CLAUDE_SKILLS_DIR) ]; then \
		echo "  Linked to: $$(readlink $(CLAUDE_SKILLS_DIR))"; \
	elif [ -d $(CLAUDE_SKILLS_DIR) ]; then \
		echo "  $(YELLOW)Warning: skills directory is not a symlink$(NC)"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Codex CLI:$(NC)"
	@echo "  Agents directory: $(CODEX_AGENTS_DIR)"
	@if [ -d $(CODEX_AGENTS_DIR) ]; then \
		total=$$(ls -1 $(CODEX_AGENTS_DIR)/*.md 2>/dev/null | wc -l); \
		installed=0; \
		skills_total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l); \
		for agent in $(AGENT_FILES); do \
			basename=$$(basename $$agent); \
			if [ -f $(CODEX_AGENTS_DIR)/$$basename ] || [ -L $(CODEX_AGENTS_DIR)/$$basename ]; then \
				installed=$$((installed + 1)); \
			fi; \
		done; \
		echo "  Omics-skills agents: $$installed/$(AGENT_COUNT) installed ($$total total in directory)"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "  Skills directory: $(CODEX_SKILLS_DIR)"
	@if [ -L $(CODEX_SKILLS_DIR) ]; then \
		echo "  Linked to: $$(readlink $(CODEX_SKILLS_DIR))"; \
	elif [ -d $(CODEX_SKILLS_DIR) ]; then \
		echo "  $(YELLOW)Warning: Codex skills directory is not a symlink$(NC)"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "  CodexLoop launcher: $(CODEXLOOP_LAUNCHER)"
	@if [ -x $(CODEXLOOP_LAUNCHER) ]; then \
		echo "  $(GREEN)✓$(NC) Installed"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi

##@ Testing

test: ## Test repository structure and installation
	@$(SCRIPTS_DIR)/test-install.sh
	@python3 -m unittest discover -s tests -v

##@ Maintenance

clean: ## Remove backup files
	@echo "$(BLUE)Cleaning backup files...$(NC)"
	@find $(CLAUDE_AGENTS_DIR) -name "*.bak" -delete 2>/dev/null || true
	@find $(AGENTS_SKILLS_DIR) -name "*.bak" -delete 2>/dev/null || true
	@find $(CODEX_AGENTS_DIR) -name "*.bak" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Backup files removed$(NC)"

update: ## Update symlinks (if using symlink method)
ifeq ($(INSTALL_METHOD),symlink)
	@echo "$(BLUE)Updating symlinks...$(NC)"
	@$(MAKE) --no-print-directory install
else
	@echo "$(YELLOW)Not using symlinks. Run 'make install INSTALL_METHOD=symlink' to switch.$(NC)"
endif

validate: ## Validate installation
	@echo "$(BLUE)Validating installation...$(NC)"
	@errors=0; \
	for agent in omics-scientist literature-expert science-writer dataviz-artist codexloop; do \
		if ! [ -f $(CLAUDE_AGENTS_DIR)/$$agent.md ]; then \
			echo "  $(RED)✗$(NC) Missing: $$agent.md in Claude Code"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	for skill in bio-logic bio-foundation-housekeeping bio-reads-qc-mapping; do \
		if ! [ -d $(AGENTS_SKILLS_DIR)/$$skill ]; then \
			echo "  $(RED)✗$(NC) Missing: $$skill in shared skills"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	if [ $$errors -eq 0 ]; then \
		echo "  $(GREEN)✓$(NC) Installation valid"; \
	else \
		echo "  $(RED)✗$(NC) Found $$errors errors"; \
		exit 1; \
	fi
