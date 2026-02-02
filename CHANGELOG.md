# Changelog

All notable changes to Omics Skills will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Three expert agents** orchestrating 20 specialized skills:
  - `omics-scientist.md` - Bioinformatics workflows (14 bio-* skills)
  - `science-writer.md` - Scientific writing and literature (5 skills)
  - `dataviz-artist.md` - Data visualization (5 skills)
- **Twenty specialized skills** across domains:
  - 14 bio-* skills (reads QC, assembly, annotation, phylogenomics, etc.)
  - 5 writing skills (literature search, manuscript generation)
  - 5 visualization skills (notebooks, static plots, dashboards)
- **Comprehensive installation system**:
  - `Makefile` - Primary installation interface with 15+ targets
  - `scripts/install.sh` - Quick install alternative
  - `scripts/uninstall.sh` - Clean removal
  - `scripts/test-install.sh` - Validation testing
- **Installation features**:
  - Symlink (default) or copy installation methods
  - Selective installation (Claude Code, Codex, or both)
  - Automatic backup of existing files
  - Status checking and validation (`make status`, `make test`)
  - Python dependency installation (`make install-python-deps`)
- **Complete documentation**:
  - `README.md` - Professional overview with agent-to-skill mappings
  - `AGENTS.md` - Guidance for AI coding agents working with repository
  - `INSTALL.md` - Detailed installation guide with troubleshooting
  - `CONTRIBUTING.md` - Contribution guidelines for adding skills/agents
  - `CHANGELOG.md` - Version history

### Changed
- Reorganized repository structure:
  - Moved shell scripts to `scripts/` directory for cleaner root
  - Simplified README focusing on Makefile as primary method
  - Enhanced README with badges and quick links
  - Updated all documentation to reference `scripts/` paths

### Fixed
- n/a (initial release)

## [1.0.0] - YYYY-MM-DD (Initial Release)

### Added
- Initial repository structure
- 3 expert agents
- 20 specialized skills
- Complete installation system
- Comprehensive documentation

---

## Version History

- **Unreleased** - Development version
- **1.0.0** - Initial public release
