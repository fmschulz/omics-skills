# Installation Guide

Complete guide for installing Omics Skills for Claude Code and Codex CLI.

---

## Prerequisites

### Required
- **Claude Code CLI** or **Codex CLI** installed
- **Git** for cloning the repository
- **Bash** shell (Linux, macOS, WSL on Windows)

### Optional
- **Python 3** with pip3 (required for some skills with Python dependencies)
- **Make** (for using Makefile, or use install.sh script instead)

### Check Prerequisites

```bash
# Check if Claude Code is installed
claude --version

# Check if Codex is installed
codex --version

# Check Python (optional, needed for some skills)
python3 --version
pip3 --version
```

---

## Installation Methods

### Method 1: Makefile (Recommended)

**For both platforms:**
```bash
make install
```

**For Claude Code only:**
```bash
make install-claude
```

**For Codex CLI only:**
```bash
make install-codex
```

**Use copies instead of symlinks:**
```bash
make install INSTALL_METHOD=copy
```

**Additional Makefile commands:**
```bash
make help              # Show all available commands
make status            # Check installation status
make test              # Run installation tests
make validate          # Validate installation
make check-deps        # Check prerequisites
make install-python-deps  # Install Python dependencies for skills
```

### Method 2: Shell Scripts

If you prefer not to use Make, shell scripts are available in `scripts/`:

```bash
# Install
scripts/install.sh           # Both platforms
scripts/install.sh --claude  # Claude Code only
scripts/install.sh --codex   # Codex only
scripts/install.sh --copy    # Use copies instead of symlinks

# Uninstall
scripts/uninstall.sh

# Test
scripts/test-install.sh
```

### Method 3: Manual Installation

**Shared skills (used by Claude and Codex):**
```bash
# Create directories
mkdir -p ~/.agents/skills

# Install skills (using symlinks)
for skill in $(pwd)/skills/*; do
    ln -sf "$skill" ~/.agents/skills/$(basename "$skill")
done
```

**For Claude Code:**
```bash
# Create directories
mkdir -p ~/.claude/agents

# Install agents (using symlinks)
ln -sf $(pwd)/agents/omics-scientist.md ~/.claude/agents/
ln -sf $(pwd)/agents/science-writer.md ~/.claude/agents/
ln -sf $(pwd)/agents/dataviz-artist.md ~/.claude/agents/

# Link shared skills
ln -sfn ~/.agents/skills ~/.claude/skills
```

**For Codex CLI:**
```bash
# Create directories
mkdir -p ~/.codex/agents

# Install agents (using symlinks)
ln -sf $(pwd)/agents/omics-scientist.md ~/.codex/agents/
ln -sf $(pwd)/agents/science-writer.md ~/.codex/agents/
ln -sf $(pwd)/agents/dataviz-artist.md ~/.codex/agents/
```

---

## Installation Options

### Symlinks vs Copies

**Symlinks (Default, Recommended):**
- ✅ Always up-to-date with repository changes
- ✅ Minimal disk space usage
- ✅ Easy updates: just `git pull`
- ✅ Single source of truth
- ⚠️ Requires keeping repository directory

**Copies:**
- ✅ Independent of repository location
- ✅ Can delete repository after install
- ⚠️ Manual reinstall needed for updates
- ⚠️ Uses more disk space

**How to switch:**
```bash
# Switch to symlinks (recommended)
make uninstall
make install INSTALL_METHOD=symlink

# Switch to copies
make uninstall
make install INSTALL_METHOD=copy
```

---

## What Gets Installed

### Directory Structure

After installation, you'll have:

```
~/.claude/
├── agents/
│   ├── omics-scientist.md          → (symlink/copy)
│   ├── science-writer.md           → (symlink/copy)
│   └── dataviz-artist.md           → (symlink/copy)
└── skills/
    ├── bio-logic/                  → (symlink/copy)
    ├── bio-foundation-housekeeping/ → (symlink/copy)
    ├── bio-reads-qc-mapping/       → (symlink/copy)
    └── ... (17 more skills)

~/.codex/
├── agents/
│   ├── omics-scientist.md          → (symlink/copy)
│   ├── science-writer.md           → (symlink/copy)
│   └── dataviz-artist.md           → (symlink/copy)
└── skills/
    ├── bio-logic/                  → (symlink/copy)
    └── ... (21 more skills)
```

### Agents Installed (3)
1. **omics-scientist.md** - Bioinformatics workflows
2. **science-writer.md** - Scientific writing
3. **dataviz-artist.md** - Data visualization

### Skills Installed (22)
1. bio-logic
2. bio-foundation-housekeeping
3. bio-reads-qc-mapping
4. bio-assembly-qc
5. bio-binning-qc
6. bio-gene-calling
7. bio-annotation
8. bio-phylogenomics
9. bio-protein-clustering-pangenome
10. bio-structure-annotation
11. bio-viromics
12. bio-stats-ml-reporting
13. bio-workflow-methods-docwriter
14. bio-prefect-dask-nextflow
15. jgi-lakehouse
16. tracking-taxonomy-updates
17. polars-dovmed
18. science-writing
19. agent-browser
20. notebook-ai-agents-skill
21. beautiful-data-viz
22. plotly-dashboard-skill

---

## Verification

### Check Installation Status

**Using Makefile:**
```bash
make status
```

**Expected output:**
```
Installation Status

Shared Skills:
  Skills directory: /home/user/.agents/skills
  Omics-skills skills: 22/22 installed (69 total in directory)

Claude Code:
  Agents directory: /home/user/.claude/agents
  Omics-skills agents: 3/3 installed (20 total in directory)
    ✓ omics-scientist.md (symlink)
    ✓ science-writer.md (symlink)
    ✓ dataviz-artist.md (symlink)

  Skills directory: /home/user/.claude/skills
  Linked to: /home/user/.agents/skills

Codex CLI:
  Agents directory: /home/user/.codex/agents
  Omics-skills agents: 3/3 installed (9 total in directory)

  Skills directory: /home/user/.agents/skills (shared)
```

### Validate Installation

**Using Makefile:**
```bash
make validate
```

This checks that all required agents and skills are properly installed.

### Manual Verification

```bash
# Check agents
ls -la ~/.claude/agents/omics-scientist.md
ls -la ~/.claude/agents/science-writer.md
ls -la ~/.claude/agents/dataviz-artist.md

# Check skills
ls -la ~/.agents/skills/bio-logic/
ls -la ~/.agents/skills/science-writing/

# Check if symlinks (should show -> pointing to source)
file ~/.claude/agents/omics-scientist.md
ls -la ~/.claude/skills
```

---

## Usage After Installation

### Claude Code

**Invoke an agent:**
```bash
# From any directory
claude --agent omics-scientist
claude --agent science-writer
claude --agent dataviz-artist

# In a project directory
cd /path/to/project
claude --agent omics-scientist
```

**List available agents:**
```bash
claude --list-agents
# Or manually:
ls -la ~/.claude/agents/
```

### Codex CLI

**Use agent as system prompt:**
```bash
codex --system-prompt ~/.codex/agents/omics-scientist.md
```

**Add to Codex config:**
```bash
# Edit ~/.codex/config.toml
[default]
system_prompt = "~/.codex/agents/omics-scientist.md"
```

---

## Python Dependencies

Some skills require Python packages. Install them with:

**Using Makefile:**
```bash
make install-python-deps
```

**Manual installation:**
```bash
# Only bio-workflow-methods-docwriter has Python deps
pip3 install -r skills/bio-workflow-methods-docwriter/requirements.txt
```

**Dependencies installed:**
- `pyyaml` - YAML parsing
- `jsonschema` - Schema validation

---

## Troubleshooting

### "Permission denied" when running scripts

```bash
chmod +x scripts/*.sh
scripts/install.sh
```

### "Command not found: make"

Use the install script instead:
```bash
./install.sh
```

Or install make:
```bash
# Ubuntu/Debian
sudo apt-get install make

# macOS
xcode-select --install
```

### "Agent not found" when invoking

Check installation:
```bash
make status
# Or manually:
ls -la ~/.claude/agents/
```

If missing, reinstall:
```bash
make install-claude
```

### Symlinks broken after moving repository

If you move the repository, symlinks will break. Options:

**Option 1: Update symlinks**
```bash
cd /new/path/to/omics-skills
make install
```

**Option 2: Switch to copies**
```bash
cd /new/path/to/omics-skills
make uninstall
make install INSTALL_METHOD=copy
```

### Skills not loading in Claude Code

Check that skills directory exists and contains the skills:
```bash
ls -la ~/.agents/skills/
```

Verify Claude Code can access the directory:
```bash
claude --list-skills
```

### Existing agents/skills will be overwritten

The installer backs up existing files with `.bak` extension:
```bash
# Your original files are saved as:
~/.claude/agents/omics-scientist.md.bak
~/.agents/skills/bio-logic.bak
```

To restore:
```bash
mv ~/.claude/agents/omics-scientist.md.bak ~/.claude/agents/omics-scientist.md
```

---

## Updating

### With Symlinks (Recommended)

```bash
cd omics-skills
git pull
# Done! Symlinks automatically point to updated code
```

### With Copies

```bash
cd omics-skills
git pull
make install INSTALL_METHOD=copy
```

### Update to Latest Version

```bash
cd omics-skills
git pull origin main
make update  # If using symlinks
```

---

## Uninstallation

### Using Makefile

```bash
# Uninstall from both platforms
make uninstall

# Uninstall from specific platform
make uninstall-claude
make uninstall-codex

# Clean backup files
make clean
```

### Using Shell Scripts

```bash
scripts/uninstall.sh                # Both platforms
scripts/uninstall.sh --claude       # Claude Code only
scripts/uninstall.sh --codex        # Codex only
scripts/uninstall.sh --keep-backups # Preserve backups
```

### Manual Uninstallation

```bash
# Remove agents
rm ~/.claude/agents/omics-scientist.md
rm ~/.claude/agents/science-writer.md
rm ~/.claude/agents/dataviz-artist.md

# Remove skills
rm -rf ~/.agents/skills/bio-logic
rm -rf ~/.agents/skills/bio-foundation-housekeeping
# ... repeat for all skills

# Or remove entire directories (if you only have omics-skills)
rm -rf ~/.claude/agents ~/.codex/agents
rm -rf ~/.agents/skills
rm -f ~/.claude/skills
```

---

## Advanced Configuration

### Selective Installation

Install only specific components:

```bash
# Install only agents
make install-claude-agents
make install-codex-agents

# Install only skills
make install-skills
make link-claude-skills
```

### Custom Installation Locations

Edit the Makefile to change installation directories:

```makefile
CLAUDE_AGENTS_DIR := /custom/path/agents
CLAUDE_SKILLS_DIR := /custom/path/skills-link
AGENTS_SKILLS_DIR := /custom/path/skills
```

### Multiple Installations

You can maintain multiple installations by cloning to different directories:

```bash
# Production version
git clone https://github.com/user/omics-skills.git ~/omics-skills-prod
cd ~/omics-skills-prod
./install.sh

# Development version
git clone https://github.com/user/omics-skills.git ~/omics-skills-dev
cd ~/omics-skills-dev
git checkout develop
./install.sh
```

The last installation will take precedence.

---

## Support

**Installation Issues:**
- Check this guide first
- Run `make validate` to diagnose
- Check permissions: `ls -la ~/.claude`

**Platform-Specific Issues:**
- Claude Code: https://github.com/anthropics/claude-code
- Codex CLI: https://codex.anthropic.com

**Repository Issues:**
- Open an issue on GitHub
- Include output of `make status`
