# Omics Skills Installer
# Installs agents and skills for Claude Code and Codex CLI

.PHONY: help install install-claude install-codex install-agents install-skills \
        uninstall uninstall-claude uninstall-codex status check-deps clean test

# Directories
AGENTS_DIR := $(CURDIR)/agents
SKILLS_DIR := $(CURDIR)/skills
SCRIPTS_DIR := $(CURDIR)/scripts

# Specific agent files (not all .md files in agents/)
AGENT_FILES := omics-scientist.md science-writer.md dataviz-artist.md

# Installation targets
CLAUDE_HOME := $(HOME)/.claude
CLAUDE_AGENTS_DIR := $(CLAUDE_HOME)/agents
CLAUDE_SKILLS_DIR := $(CLAUDE_HOME)/skills

CODEX_HOME := $(HOME)/.codex
CODEX_AGENTS_DIR := $(CODEX_HOME)/agents
CODEX_SKILLS_DIR := $(CODEX_HOME)/skills

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

install-claude: install-claude-agents install-claude-skills ## Install for Claude Code only
	@echo "$(GREEN)✓ Claude Code installation complete$(NC)"

install-codex: install-codex-agents install-codex-skills ## Install for Codex CLI only
	@echo "$(GREEN)✓ Codex CLI installation complete$(NC)"

install-claude-agents: ## Install agents to Claude Code
	@echo "$(BLUE)Installing agents to Claude Code...$(NC)"
	@mkdir -p $(CLAUDE_AGENTS_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		target=$(CLAUDE_AGENTS_DIR)/$$agent; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -L $$target ]; then \
			echo "  Updating symlink: $$agent"; \
			rm $$target; \
		elif [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$agent exists (backing up)$(NC)"; \
			mv $$target $$target.bak; \
		fi; \
		ln -sf $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$agent"; \
	done
else
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		target=$(CLAUDE_AGENTS_DIR)/$$agent; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$agent exists (backing up)$(NC)"; \
			cp $$target $$target.bak; \
		fi; \
		cp $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$agent"; \
	done
endif

install-claude-skills: ## Install skills to Claude Code
	@echo "$(BLUE)Installing skills to Claude Code...$(NC)"
	@mkdir -p $(CLAUDE_SKILLS_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d | wc -l); \
	current=0; \
	for skill in $(SKILLS_DIR)/*; do \
		if [ -d $$skill ]; then \
			current=$$((current + 1)); \
			basename=$$(basename $$skill); \
			target=$(CLAUDE_SKILLS_DIR)/$$basename; \
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
			target=$(CLAUDE_SKILLS_DIR)/$$basename; \
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

install-codex-agents: ## Install agents to Codex CLI
	@echo "$(BLUE)Installing agents to Codex CLI...$(NC)"
	@mkdir -p $(CODEX_AGENTS_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		target=$(CODEX_AGENTS_DIR)/$$agent; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -L $$target ]; then \
			echo "  Updating symlink: $$agent"; \
			rm $$target; \
		elif [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$agent exists (backing up)$(NC)"; \
			mv $$target $$target.bak; \
		fi; \
		ln -sf $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$agent"; \
	done
else
	@for agent in $(AGENT_FILES); do \
		agent_path=$(AGENTS_DIR)/$$agent; \
		target=$(CODEX_AGENTS_DIR)/$$agent; \
		if [ ! -f $$agent_path ]; then \
			echo "  $(RED)✗$(NC) $$agent not found"; \
			continue; \
		fi; \
		if [ -f $$target ]; then \
			echo "  $(YELLOW)Warning: $$agent exists (backing up)$(NC)"; \
			cp $$target $$target.bak; \
		fi; \
		cp $$agent_path $$target; \
		echo "  $(GREEN)✓$(NC) $$agent"; \
	done
endif

install-codex-skills: ## Install skills to Codex CLI
	@echo "$(BLUE)Installing skills to Codex CLI...$(NC)"
	@mkdir -p $(CODEX_SKILLS_DIR)
ifeq ($(INSTALL_METHOD),symlink)
	@total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d | wc -l); \
	current=0; \
	for skill in $(SKILLS_DIR)/*; do \
		if [ -d $$skill ]; then \
			current=$$((current + 1)); \
			basename=$$(basename $$skill); \
			target=$(CODEX_SKILLS_DIR)/$$basename; \
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
			target=$(CODEX_SKILLS_DIR)/$$basename; \
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

##@ Dependencies

check-deps: ## Check if required commands are available
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v claude >/dev/null 2>&1 && echo "  $(GREEN)✓$(NC) Claude Code CLI found" || echo "  $(YELLOW)○$(NC) Claude Code CLI not found (install from https://claude.com/claude-code)"
	@command -v codex >/dev/null 2>&1 && echo "  $(GREEN)✓$(NC) Codex CLI found" || echo "  $(YELLOW)○$(NC) Codex CLI not found (optional)"
	@command -v python3 >/dev/null 2>&1 && echo "  $(GREEN)✓$(NC) Python 3 found" || echo "  $(YELLOW)○$(NC) Python 3 not found (required for some skills)"
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

uninstall: uninstall-claude uninstall-codex ## Uninstall from both platforms
	@echo "$(GREEN)✓ Uninstallation complete$(NC)"

uninstall-claude: ## Uninstall from Claude Code
	@echo "$(BLUE)Uninstalling from Claude Code...$(NC)"
	@current=0; \
	for agent in $(AGENT_FILES); do \
		target=$(CLAUDE_AGENTS_DIR)/$$agent; \
		if [ -L $$target ] || [ -f $$target ]; then \
			current=$$((current + 1)); \
			rm $$target; \
			if [ "$(VERBOSE)" = "1" ]; then \
				echo "  [$$current/3] $(GREEN)✓$(NC) Removed $$agent"; \
			else \
				printf "\r  Agents: $$current/3"; \
			fi; \
		fi; \
	done; \
	if [ "$(VERBOSE)" != "1" ]; then \
		printf "\r  $(GREEN)✓$(NC) Removed: $$current/3 agents\n"; \
	else \
		echo "  $(GREEN)✓$(NC) Completed: $$current/3 agents"; \
	fi
	@total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d | wc -l); \
	current=0; \
	for skill in $(SKILLS_DIR)/*; do \
		if [ -d $$skill ]; then \
			basename=$$(basename $$skill); \
			target=$(CLAUDE_SKILLS_DIR)/$$basename; \
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
	@echo "$(GREEN)✓ Claude Code uninstalled$(NC)"

uninstall-codex: ## Uninstall from Codex CLI
	@echo "$(BLUE)Uninstalling from Codex CLI...$(NC)"
	@current=0; \
	for agent in $(AGENT_FILES); do \
		target=$(CODEX_AGENTS_DIR)/$$agent; \
		if [ -L $$target ] || [ -f $$target ]; then \
			current=$$((current + 1)); \
			rm $$target; \
			if [ "$(VERBOSE)" = "1" ]; then \
				echo "  [$$current/3] $(GREEN)✓$(NC) Removed $$agent"; \
			else \
				printf "\r  Agents: $$current/3"; \
			fi; \
		fi; \
	done; \
	if [ "$(VERBOSE)" != "1" ]; then \
		printf "\r  $(GREEN)✓$(NC) Removed: $$current/3 agents\n"; \
	else \
		echo "  $(GREEN)✓$(NC) Completed: $$current/3 agents"; \
	fi
	@total=$$(find $(SKILLS_DIR) -mindepth 1 -maxdepth 1 -type d | wc -l); \
	current=0; \
	for skill in $(SKILLS_DIR)/*; do \
		if [ -d $$skill ]; then \
			basename=$$(basename $$skill); \
			target=$(CODEX_SKILLS_DIR)/$$basename; \
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
	@echo "$(GREEN)✓ Codex CLI uninstalled$(NC)"

##@ Status

status: ## Show installation status
	@echo "$(BLUE)Installation Status$(NC)"
	@echo ""
	@echo "$(YELLOW)Claude Code:$(NC)"
	@echo "  Agents directory: $(CLAUDE_AGENTS_DIR)"
	@if [ -d $(CLAUDE_AGENTS_DIR) ]; then \
		total=$$(ls -1 $(CLAUDE_AGENTS_DIR)/*.md 2>/dev/null | wc -l); \
		installed=0; \
		for agent in $(AGENT_FILES); do \
			if [ -f $(CLAUDE_AGENTS_DIR)/$$agent ] || [ -L $(CLAUDE_AGENTS_DIR)/$$agent ]; then \
				installed=$$((installed + 1)); \
			fi; \
		done; \
		echo "  Omics-skills agents: $$installed/3 installed ($$total total in directory)"; \
		for agent in $(AGENT_FILES); do \
			if [ -f $(CLAUDE_AGENTS_DIR)/$$agent ] || [ -L $(CLAUDE_AGENTS_DIR)/$$agent ]; then \
				if [ -L $(CLAUDE_AGENTS_DIR)/$$agent ]; then \
					echo "    $(GREEN)✓$(NC) $$agent (symlink)"; \
				else \
					echo "    $(GREEN)✓$(NC) $$agent (copy)"; \
				fi; \
			else \
				echo "    $(RED)✗$(NC) $$agent"; \
			fi; \
		done; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "  Skills directory: $(CLAUDE_SKILLS_DIR)"
	@if [ -d $(CLAUDE_SKILLS_DIR) ]; then \
		total=$$(find $(CLAUDE_SKILLS_DIR) -mindepth 1 -maxdepth 1 \( -type d -o -type l \) 2>/dev/null | wc -l); \
		installed=0; \
		for skill in $(SKILLS_DIR)/*; do \
			if [ -d $$skill ]; then \
				basename=$$(basename $$skill); \
				if [ -d $(CLAUDE_SKILLS_DIR)/$$basename ] || [ -L $(CLAUDE_SKILLS_DIR)/$$basename ]; then \
					installed=$$((installed + 1)); \
				fi; \
			fi; \
		done; \
		echo "  Omics-skills skills: $$installed/20 installed ($$total total in directory)"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Codex CLI:$(NC)"
	@echo "  Agents directory: $(CODEX_AGENTS_DIR)"
	@if [ -d $(CODEX_AGENTS_DIR) ]; then \
		total=$$(ls -1 $(CODEX_AGENTS_DIR)/*.md 2>/dev/null | wc -l); \
		installed=0; \
		for agent in $(AGENT_FILES); do \
			if [ -f $(CODEX_AGENTS_DIR)/$$agent ] || [ -L $(CODEX_AGENTS_DIR)/$$agent ]; then \
				installed=$$((installed + 1)); \
			fi; \
		done; \
		echo "  Omics-skills agents: $$installed/3 installed ($$total total in directory)"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi
	@echo ""
	@echo "  Skills directory: $(CODEX_SKILLS_DIR)"
	@if [ -d $(CODEX_SKILLS_DIR) ]; then \
		total=$$(find $(CODEX_SKILLS_DIR) -mindepth 1 -maxdepth 1 \( -type d -o -type l \) 2>/dev/null | wc -l); \
		installed=0; \
		for skill in $(SKILLS_DIR)/*; do \
			if [ -d $$skill ]; then \
				basename=$$(basename $$skill); \
				if [ -d $(CODEX_SKILLS_DIR)/$$basename ] || [ -L $(CODEX_SKILLS_DIR)/$$basename ]; then \
					installed=$$((installed + 1)); \
				fi; \
			fi; \
		done; \
		echo "  Omics-skills skills: $$installed/20 installed ($$total total in directory)"; \
	else \
		echo "  $(RED)Not installed$(NC)"; \
	fi

##@ Testing

test: ## Test repository structure and installation
	@$(SCRIPTS_DIR)/test-install.sh

##@ Maintenance

clean: ## Remove backup files
	@echo "$(BLUE)Cleaning backup files...$(NC)"
	@find $(CLAUDE_AGENTS_DIR) -name "*.bak" -delete 2>/dev/null || true
	@find $(CLAUDE_SKILLS_DIR) -name "*.bak" -delete 2>/dev/null || true
	@find $(CODEX_AGENTS_DIR) -name "*.bak" -delete 2>/dev/null || true
	@find $(CODEX_SKILLS_DIR) -name "*.bak" -delete 2>/dev/null || true
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
	for agent in omics-scientist science-writer dataviz-artist; do \
		if ! [ -f $(CLAUDE_AGENTS_DIR)/$$agent.md ]; then \
			echo "  $(RED)✗$(NC) Missing: $$agent.md in Claude Code"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	for skill in bio-logic bio-foundation-housekeeping bio-reads-qc-mapping; do \
		if ! [ -d $(CLAUDE_SKILLS_DIR)/$$skill ]; then \
			echo "  $(RED)✗$(NC) Missing: $$skill in Claude Code"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	if [ $$errors -eq 0 ]; then \
		echo "  $(GREEN)✓$(NC) Installation valid"; \
	else \
		echo "  $(RED)✗$(NC) Found $$errors errors"; \
		exit 1; \
	fi
