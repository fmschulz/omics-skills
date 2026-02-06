#!/usr/bin/env bash
# Omics Skills Quick Installer
# Simple alternative to Makefile for quick installation

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# If running from scripts/ directory, go up one level
if [[ "$(basename "$SCRIPT_DIR")" == "scripts" ]]; then
    REPO_ROOT="$(dirname "$SCRIPT_DIR")"
else
    REPO_ROOT="$SCRIPT_DIR"
fi
AGENTS_DIR="$REPO_ROOT/agents"
SKILLS_DIR="$REPO_ROOT/skills"

# Specific agent files
AGENT_FILES=("omics-scientist.md" "science-writer.md" "dataviz-artist.md")

CLAUDE_AGENTS_DIR="$HOME/.claude/agents"
CODEX_AGENTS_DIR="$HOME/.codex/agents"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
AGENTS_SKILLS_DIR="$HOME/.agents/skills"

# Installation method (symlink by default, use --copy to copy files)
INSTALL_METHOD="symlink"

# Parse arguments
INSTALL_TARGET="both"
while [[ $# -gt 0 ]]; do
    case $1 in
        --claude)
            INSTALL_TARGET="claude"
            shift
            ;;
        --codex)
            INSTALL_TARGET="codex"
            shift
            ;;
        --copy)
            INSTALL_METHOD="copy"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --claude    Install for Claude Code only"
            echo "  --codex     Install for Codex CLI only"
            echo "  --copy      Copy files instead of creating symlinks"
            echo "  --help      Show this help message"
            echo ""
            echo "Default: Install for both platforms using symlinks"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Functions
install_agents() {
    local target_dir=$1
    local platform=$2

    echo -e "${BLUE}Installing agents to $platform...${NC}"
    mkdir -p "$target_dir"

    for agent in "${AGENT_FILES[@]}"; do
        agent_path="$AGENTS_DIR/$agent"
        basename=$(basename "$agent")
        target="$target_dir/$basename"

        if [ ! -f "$agent_path" ]; then
            echo -e "  ${RED}✗${NC} $agent not found"
            continue
        fi

        if [ -L "$target" ]; then
            echo "  Updating symlink: $basename"
            rm "$target"
        elif [ -f "$target" ]; then
            echo -e "  ${YELLOW}Warning: $basename exists (backing up)${NC}"
            mv "$target" "$target.bak"
        fi

        if [ "$INSTALL_METHOD" = "symlink" ]; then
            ln -sf "$agent_path" "$target"
        else
            cp "$agent_path" "$target"
        fi

        echo -e "  ${GREEN}✓${NC} $basename"
    done
}

install_skills() {
    local target_dir=$1
    local platform=$2

    echo -e "${BLUE}Installing skills to $platform...${NC}"
    mkdir -p "$target_dir"

    for skill in "$SKILLS_DIR"/*; do
        if [ -d "$skill" ]; then
            basename=$(basename "$skill")
            target="$target_dir/$basename"

            if [ -L "$target" ]; then
                echo "  Updating symlink: $basename"
                rm "$target"
            elif [ -d "$target" ]; then
                echo -e "  ${YELLOW}Warning: $basename exists (backing up)${NC}"
                mv "$target" "$target.bak"
            fi

            if [ "$INSTALL_METHOD" = "symlink" ]; then
                ln -sf "$skill" "$target"
            else
                cp -r "$skill" "$target"
            fi

            echo -e "  ${GREEN}✓${NC} $basename"
        fi
    done
}

link_claude_skills() {
    echo -e "${BLUE}Linking Claude skills to $AGENTS_SKILLS_DIR...${NC}"
    mkdir -p "$HOME/.claude"

    if [ -L "$CLAUDE_SKILLS_DIR" ]; then
        ln -sfn "$AGENTS_SKILLS_DIR" "$CLAUDE_SKILLS_DIR"
    elif [ -e "$CLAUDE_SKILLS_DIR" ]; then
        backup="$CLAUDE_SKILLS_DIR.bak"
        if [ -e "$backup" ]; then
            backup="$CLAUDE_SKILLS_DIR.bak.$(date +%s)"
        fi
        mv "$CLAUDE_SKILLS_DIR" "$backup"
        ln -sfn "$AGENTS_SKILLS_DIR" "$CLAUDE_SKILLS_DIR"
        echo -e "  ${YELLOW}Backed up existing skills to $backup${NC}"
    else
        ln -sfn "$AGENTS_SKILLS_DIR" "$CLAUDE_SKILLS_DIR"
    fi

    echo -e "  ${GREEN}✓${NC} $CLAUDE_SKILLS_DIR -> $AGENTS_SKILLS_DIR"
}

check_deps() {
    echo -e "${BLUE}Checking dependencies...${NC}"

    if command -v claude >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Claude Code CLI found"
    else
        echo -e "  ${YELLOW}○${NC} Claude Code CLI not found"
        echo "    Install from https://claude.com/claude-code"
    fi

    if command -v codex >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Codex CLI found"
    else
        echo -e "  ${YELLOW}○${NC} Codex CLI not found (optional)"
    fi

    if command -v python3 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Python 3 found"
    else
        echo -e "  ${YELLOW}○${NC} Python 3 not found (required for some skills)"
    fi

    echo ""
}

show_status() {
    echo -e "${BLUE}Installation Status${NC}"
    echo ""
    skills_total=$(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)

    echo -e "${YELLOW}Shared Skills:${NC}"
    echo "  Skills directory: $AGENTS_SKILLS_DIR"
    if [ -d "$AGENTS_SKILLS_DIR" ]; then
        count=$(find -L "$AGENTS_SKILLS_DIR" -maxdepth 1 -type d -o -type l 2>/dev/null | tail -n +2 | wc -l)
        echo "  Installed skills: $count/$skills_total"
    else
        echo -e "  ${RED}Not installed${NC}"
    fi

    echo ""
    echo -e "${YELLOW}Claude Code:${NC}"
    echo "  Agents directory: $CLAUDE_AGENTS_DIR"
    if [ -d "$CLAUDE_AGENTS_DIR" ]; then
        count=$(find "$CLAUDE_AGENTS_DIR" -name "*.md" 2>/dev/null | wc -l)
        echo "  Installed agents: $count/3"
    else
        echo -e "  ${RED}Not installed${NC}"
    fi

    echo "  Skills directory: $CLAUDE_SKILLS_DIR"
    if [ -L "$CLAUDE_SKILLS_DIR" ]; then
        echo "  Linked to: $(readlink "$CLAUDE_SKILLS_DIR")"
    elif [ -d "$CLAUDE_SKILLS_DIR" ]; then
        echo -e "  ${YELLOW}Warning: skills directory is not a symlink${NC}"
    else
        echo -e "  ${RED}Not installed${NC}"
    fi

    echo ""
    echo -e "${YELLOW}Codex CLI:${NC}"
    echo "  Agents directory: $CODEX_AGENTS_DIR"
    if [ -d "$CODEX_AGENTS_DIR" ]; then
        count=$(find "$CODEX_AGENTS_DIR" -name "*.md" 2>/dev/null | wc -l)
        echo "  Installed agents: $count/3"
    else
        echo -e "  ${RED}Not installed${NC}"
    fi

    echo "  Skills directory: $AGENTS_SKILLS_DIR (shared)"
}

# Main installation
echo -e "${BLUE}╔═══════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Omics Skills Installer          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════╝${NC}"
echo ""

check_deps

if [ "$INSTALL_METHOD" = "symlink" ]; then
    echo -e "${BLUE}Installation method: Symlinks${NC}"
    echo -e "  ${GREEN}Benefits:${NC} Always up-to-date, minimal disk space"
else
    echo -e "${BLUE}Installation method: Copy${NC}"
    echo -e "  ${YELLOW}Note:${NC} You'll need to re-run installer to get updates"
fi
echo ""

# Install based on target
install_skills "$AGENTS_SKILLS_DIR" "Shared skills"
echo ""

if [ "$INSTALL_TARGET" = "both" ] || [ "$INSTALL_TARGET" = "claude" ]; then
    install_agents "$CLAUDE_AGENTS_DIR" "Claude Code"
    link_claude_skills
    echo -e "${GREEN}✓ Claude Code installation complete${NC}"
    echo ""
fi

if [ "$INSTALL_TARGET" = "both" ] || [ "$INSTALL_TARGET" = "codex" ]; then
    install_agents "$CODEX_AGENTS_DIR" "Codex CLI"
    echo -e "${GREEN}✓ Codex CLI installation complete${NC}"
    echo "  Skills are shared from $AGENTS_SKILLS_DIR"
    echo ""
fi

echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""

show_status

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Invoke an agent:"
echo "     claude --agent omics-scientist"
echo "     claude --agent science-writer"
echo "     claude --agent dataviz-artist"
echo ""
echo "  2. Or use in Codex:"
echo "     codex --system-prompt ~/.codex/agents/omics-scientist.md"
echo ""
echo -e "${YELLOW}Tip:${NC} Use symlinks (default) to always have the latest updates"
echo "     Updates: cd $(basename "$REPO_ROOT") && git pull && ./install.sh"
