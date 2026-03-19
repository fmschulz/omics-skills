#!/usr/bin/env bash
# Test installation of omics-skills

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get repository root (parent of scripts directory if run from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(basename "$SCRIPT_DIR")" == "scripts" ]]; then
    REPO_ROOT="$(dirname "$SCRIPT_DIR")"
else
    REPO_ROOT="$SCRIPT_DIR"
fi

ERRORS=0
WARNINGS=0
SKILLS_TOTAL=$(find "$REPO_ROOT/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
AGENTS_SKILLS_DIR="$HOME/.agents/skills"
AGENTS_CATALOG_DIR="$HOME/.agents/omics-skills"

echo -e "${BLUE}╔═══════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Omics Skills Installation Test  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════╝${NC}"
echo ""

# Test 1: Check repository structure
echo -e "${BLUE}[1/9] Checking repository structure...${NC}"
if [ ! -d "$REPO_ROOT/agents" ]; then
    echo -e "  ${RED}✗${NC} agents/ directory missing"
    ERRORS=$((ERRORS + 1))
else
    echo -e "  ${GREEN}✓${NC} agents/ directory exists"
fi

if [ ! -d "$REPO_ROOT/skills" ]; then
    echo -e "  ${RED}✗${NC} skills/ directory missing"
    ERRORS=$((ERRORS + 1))
else
    echo -e "  ${GREEN}✓${NC} skills/ directory exists"
fi

# Test 2: Check agent files
echo -e "\n${BLUE}[2/9] Checking agent files...${NC}"
for agent in omics-scientist literature-expert science-writer dataviz-artist codexloop; do
    if [ ! -f "$REPO_ROOT/agents/$agent.md" ]; then
        echo -e "  ${RED}✗${NC} $agent.md missing"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "  ${GREEN}✓${NC} $agent.md exists"
    fi
done

# Test 3: Check critical skills
echo -e "\n${BLUE}[3/9] Checking critical skills...${NC}"
for skill in bio-logic bio-foundation-housekeeping scientific-writing crossref-lookup scientific-impact-assessment beautiful-data-viz codexloop; do
    if [ ! -d "$REPO_ROOT/skills/$skill" ]; then
        echo -e "  ${RED}✗${NC} $skill/ missing"
        ERRORS=$((ERRORS + 1))
    else
        if [ ! -f "$REPO_ROOT/skills/$skill/SKILL.md" ]; then
            echo -e "  ${YELLOW}⚠${NC} $skill/ exists but missing SKILL.md"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "  ${GREEN}✓${NC} $skill/ exists with SKILL.md"
        fi
    fi
done

# Test 4: Validate skill definitions
echo -e "\n${BLUE}[4/9] Validating skill definitions...${NC}"
if ! "$REPO_ROOT/scripts/validate-skills.py" >/dev/null 2>&1; then
    echo -e "  ${RED}✗${NC} Skill validation failed"
    ERRORS=$((ERRORS + 1))
else
    echo -e "  ${GREEN}✓${NC} Skill validation passed"
fi

# Test 5: Check installation scripts
echo -e "\n${BLUE}[5/9] Checking installation scripts...${NC}"
if [ ! -f "$REPO_ROOT/scripts/install.sh" ]; then
    echo -e "  ${RED}✗${NC} scripts/install.sh missing"
    ERRORS=$((ERRORS + 1))
elif [ ! -x "$REPO_ROOT/scripts/install.sh" ]; then
    echo -e "  ${YELLOW}⚠${NC} scripts/install.sh not executable"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${GREEN}✓${NC} scripts/install.sh exists and is executable"
fi

if [ ! -f "$REPO_ROOT/Makefile" ]; then
    echo -e "  ${RED}✗${NC} Makefile missing"
    ERRORS=$((ERRORS + 1))
else
    echo -e "  ${GREEN}✓${NC} Makefile exists"
fi

# Test 6: Build skill catalog
echo -e "\n${BLUE}[6/9] Building skill catalog...${NC}"
if [ ! -f "$REPO_ROOT/scripts/skill_index.py" ]; then
    echo -e "  ${RED}✗${NC} scripts/skill_index.py missing"
    ERRORS=$((ERRORS + 1))
else
    tmpdir=$(mktemp -d)
    if ! python3 "$REPO_ROOT/scripts/skill_index.py" build --repo "$REPO_ROOT" --out "$tmpdir" >/dev/null 2>&1; then
        echo -e "  ${RED}✗${NC} Catalog build failed"
        ERRORS=$((ERRORS + 1))
    else
        missing_files=0
        for file in catalog.json relationships.json routing.json; do
            if [ ! -f "$tmpdir/$file" ]; then
                echo -e "  ${RED}✗${NC} Missing $file"
                ERRORS=$((ERRORS + 1))
                missing_files=$((missing_files + 1))
            fi
        done
        if [ "$missing_files" -eq 0 ]; then
            echo -e "  ${GREEN}✓${NC} Catalog build succeeded"
        fi
    fi
    rm -rf "$tmpdir"
fi

# Test 7: Check shared installation (if exists)
echo -e "\n${BLUE}[7/9] Checking shared installation...${NC}"
if [ -d "$AGENTS_CATALOG_DIR" ]; then
    missing_files=0
    for file in skill_index.py README.md catalog.json relationships.json routing.json; do
        if [ ! -f "$AGENTS_CATALOG_DIR/$file" ] && [ ! -L "$AGENTS_CATALOG_DIR/$file" ]; then
            echo -e "  ${YELLOW}⚠${NC} Missing shared catalog file: $file"
            WARNINGS=$((WARNINGS + 1))
            missing_files=$((missing_files + 1))
        fi
    done
    if [ "$missing_files" -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Shared catalog installed"
    fi
else
    echo -e "  ${YELLOW}○${NC} Shared catalog directory not found"
fi

# Test 8: Check Claude Code installation (if exists)
echo -e "\n${BLUE}[8/9] Checking Claude Code installation...${NC}"
if [ -d "$HOME/.claude" ]; then
    echo -e "  ${GREEN}✓${NC} Claude Code directory exists"

    if [ -d "$HOME/.claude/agents" ]; then
        count=$(find "$HOME/.claude/agents" \( -name "omics-scientist.md" -o -name "literature-expert.md" -o -name "science-writer.md" -o -name "dataviz-artist.md" -o -name "codexloop.md" \) 2>/dev/null | wc -l)
        if [ "$count" -eq 5 ]; then
            echo -e "  ${GREEN}✓${NC} All 5 agents installed in Claude Code"
        elif [ "$count" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠${NC} Only $count/5 agents installed in Claude Code"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "  ${YELLOW}○${NC} No omics-skills agents in Claude Code (not installed yet)"
        fi
    else
        echo -e "  ${YELLOW}○${NC} Claude Code agents directory not found"
    fi

    if [ -d "$AGENTS_SKILLS_DIR" ]; then
        count=0
        for skill in "$REPO_ROOT/skills"/*; do
            if [ -d "$skill" ]; then
                base=$(basename "$skill")
                if [ -d "$AGENTS_SKILLS_DIR/$base" ] || [ -L "$AGENTS_SKILLS_DIR/$base" ]; then
                    count=$((count + 1))
                fi
            fi
        done
        if [ "$count" -eq "$SKILLS_TOTAL" ]; then
            echo -e "  ${GREEN}✓${NC} All $SKILLS_TOTAL skills installed in shared skills"
        elif [ "$count" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠${NC} Only $count/$SKILLS_TOTAL skills installed in shared skills"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "  ${YELLOW}○${NC} No omics-skills in shared skills (not installed yet)"
        fi
    else
        echo -e "  ${YELLOW}○${NC} Shared skills directory not found"
    fi

    if [ -L "$HOME/.claude/skills" ]; then
        target=$(readlink "$HOME/.claude/skills")
        if [ "$target" = "$AGENTS_SKILLS_DIR" ]; then
            echo -e "  ${GREEN}✓${NC} Claude skills linked to shared skills"
        else
            echo -e "  ${YELLOW}⚠${NC} Claude skills linked to $target (expected $AGENTS_SKILLS_DIR)"
            WARNINGS=$((WARNINGS + 1))
        fi
    elif [ -d "$HOME/.claude/skills" ]; then
        echo -e "  ${YELLOW}⚠${NC} Claude skills directory is not a symlink"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "  ${YELLOW}○${NC} Claude skills directory not found"
    fi
else
    echo -e "  ${YELLOW}○${NC} Claude Code not installed or not configured"
fi

# Test 9: Check Codex installation (if exists)
echo -e "\n${BLUE}[9/9] Checking Codex CLI installation...${NC}"
if [ -d "$HOME/.codex" ]; then
    echo -e "  ${GREEN}✓${NC} Codex CLI directory exists"

    if [ -d "$HOME/.codex/agents" ]; then
        count=$(find "$HOME/.codex/agents" \( -name "omics-scientist.md" -o -name "literature-expert.md" -o -name "science-writer.md" -o -name "dataviz-artist.md" -o -name "codexloop.md" \) 2>/dev/null | wc -l)
        if [ "$count" -eq 5 ]; then
            echo -e "  ${GREEN}✓${NC} All 5 agents installed in Codex"
        elif [ "$count" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠${NC} Only $count/5 agents installed in Codex"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "  ${YELLOW}○${NC} No omics-skills agents in Codex (not installed yet)"
        fi
    else
        echo -e "  ${YELLOW}○${NC} Codex agents directory not found"
    fi

    if [ -L "$HOME/.codex/skills" ]; then
        target=$(readlink "$HOME/.codex/skills")
        if [ "$target" = "$AGENTS_SKILLS_DIR" ]; then
            echo -e "  ${GREEN}✓${NC} Codex skills linked to shared skills"
        else
            echo -e "  ${YELLOW}⚠${NC} Codex skills linked to $target (expected $AGENTS_SKILLS_DIR)"
            WARNINGS=$((WARNINGS + 1))
        fi
    elif [ -d "$HOME/.codex/skills" ]; then
        echo -e "  ${YELLOW}⚠${NC} Codex skills directory is not a symlink"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "  ${YELLOW}○${NC} Codex skills directory not found"
    fi

    if [ -x "$HOME/.codex/bin/codexloop" ]; then
        echo -e "  ${GREEN}✓${NC} CodexLoop launcher installed"
    else
        echo -e "  ${YELLOW}○${NC} CodexLoop launcher not installed"
    fi
else
    echo -e "  ${YELLOW}○${NC} Codex CLI not installed or not configured"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════${NC}"
echo -e "${BLUE}Summary:${NC}"

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "  ${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Repository structure is valid."
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Run: make install"
    echo "  2. Or: scripts/install.sh"
    echo "  3. Check status: make status"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "  ${YELLOW}⚠ Tests passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Repository structure is valid but has minor issues."
    if [ ! -d "$HOME/.claude/agents" ] || [ ! -d "$HOME/.codex/agents" ]; then
        echo ""
        echo -e "${BLUE}To install:${NC}"
        echo "  make install"
        echo "  scripts/install.sh"
    fi
    exit 0
else
    echo -e "  ${RED}✗ Tests failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before proceeding."
    exit 1
fi
