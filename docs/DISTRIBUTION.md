# Distribution Guide

How to publish and disseminate omics-skills across registries, marketplaces, and ecosystems.

---

## Overview

The [Agent Skills open standard](https://agentskills.io/specification) (released December 2025) enables cross-platform skill portability. Your skills will work across Claude Code, Codex CLI, ChatGPT, and other platforms that adopt the standard.

**Good news:** Your repository already follows the Agent Skills specification! Each skill has a `SKILL.md` with YAML frontmatter, making it ready for distribution.

---

## Distribution Channels

### 1. Official Repositories

#### Anthropic Skills Repository ⭐ (Recommended)
**URL:** [github.com/anthropics/skills](https://github.com/anthropics/skills)

**Purpose:** Official Anthropic-maintained public repository for Agent Skills

**How to Submit:**
1. Fork the repository
2. Add your skill(s) to the `skills/` directory
3. Follow their structure (see existing skills as examples)
4. Test your skill with Claude Code
5. Submit a pull request with clear documentation

**Benefits:**
- Official Anthropic visibility
- Auto-indexed by Claude Code plugin marketplace
- High trust/credibility
- Direct user installation via `/plugin install skill-name`

**What to Submit:**
- Individual skills (one PR per skill, or related skills together)
- Start with high-impact skills: `bio-logic`, `scientific-writing`, `beautiful-data-viz`
- Consider submitting agent-agnostic skills first

#### OpenAI Codex Skills Repository
**URL:** [github.com/openai/skills](https://github.com/openai/skills)

**Purpose:** Skills Catalog for Codex CLI

**How to Submit:**
1. Fork the repository
2. Add skill to appropriate category
3. Follow their contribution guidelines
4. Submit pull request

**Benefits:**
- Codex CLI users can discover your skills
- Cross-platform exposure (Agent Skills standard)

### 2. Community Marketplaces

#### SkillsMP (Skills Marketplace) ⭐
**URL:** [skillsmp.com](https://skillsmp.com)

**Purpose:** Community-driven aggregator with 71,000+ skills

**How to Submit:**
- **Automatic indexing:** Push your skills to GitHub - SkillsMP automatically indexes public repositories
- **Manual submission:** Contact via their site or submit your GitHub repo URL
- **GitHub tag:** Add topic tags like `claude-skills`, `agent-skills`, `bioinformatics`

**Benefits:**
- Largest skill aggregator
- Compatible with Claude Code, Codex CLI, ChatGPT
- Search and discovery features
- No approval process needed

**Action:**
```bash
# Add GitHub topics to your repo
# Go to: https://github.com/fmschulz/omics-skills
# Add topics: claude-skills, agent-skills, bioinformatics,
#             computational-biology, scientific-writing, data-visualization
```

#### SkillHub
**URL:** [skillhub.club](https://www.skillhub.club/)

**Purpose:** AI-evaluated Claude skills marketplace (7,000+ skills)

**How to Submit:**
- Create a SKILL.md file, push to GitHub, and it's automatically indexed
- Uses AI evaluation for quality scoring
- Compatible with Claude Code, Codex CLI, Gemini CLI, OpenCode

**Benefits:**
- Quality scoring helps users find best skills
- Multi-platform support
- Automatic indexing

#### MCP Market
**URL:** [mcpmarket.com/tools/skills](https://mcpmarket.com/tools/skills)

**Purpose:** Agent Skills directory for Claude.ai, Claude Code, Codex

**How to Submit:**
- Submit via their website
- Provide GitHub repository URL
- Include skill descriptions and categories

---

## 3. Your GitHub Repository

#### Make Your Repo Discoverable

**Current URL:** [github.com/fmschulz/omics-skills](https://github.com/fmschulz/omics-skills)

**Optimize for Discovery:**

1. **Add GitHub Topics:**
   ```
   claude-skills, agent-skills, claude-code, codex-cli,
   bioinformatics, computational-biology, omics,
   scientific-writing, data-visualization, genomics
   ```

2. **Complete Repository Description:**
   ```
   4 expert agents and 35 specialized skills for bioinformatics,
   scientific writing, and data visualization. Compatible with
   Claude Code and Codex CLI.
   ```

3. **Keep README badges accurate if used:**
   - Agent Skills standard badge
   - Compatible platforms badge
   - License badge

4. **Maintain GitHub Pages:**
   - Publish the MkDocs documentation site
   - Keep installation, skill catalog, and routing pages current

#### Repository Structure for Marketplaces

Marketplaces look for:
- ✅ `SKILL.md` files with YAML frontmatter (you have this)
- ✅ Clear directory structure (you have this)
- ✅ README.md documentation (you have this)
- ✅ LICENSE file in the repository root
- ✅ GitHub topics/tags (need to add)

---

## 4. Community Listings

#### Awesome Lists

**awesome-claude-skills:**
- [github.com/travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
- [github.com/ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

**How to Submit:**
1. Fork the repository
2. Add your repository to appropriate category
3. Submit pull request with description

**Benefits:**
- Community visibility
- Curated lists are often referenced
- Good for specialized domains (bioinformatics)

#### Reddit & Forums

**Communities:**
- r/ClaudeAI
- r/Bioinformatics
- Anthropic Discord
- Bioinformatics forums

**How to Share:**
- Create announcement post
- Highlight unique value (first comprehensive omics skills collection)
- Include installation instructions
- Request feedback

---

## Step-by-Step Action Plan

### Phase 1: Immediate Actions (1-2 hours)

1. **Add GitHub Topics:**
   ```bash
   # Go to: https://github.com/fmschulz/omics-skills
   # Click "About" gear icon
   # Add topics: claude-skills, agent-skills, bioinformatics,
   #             computational-biology, scientific-writing, etc.
   ```

2. **Keep the root LICENSE file current.**

3. **Refresh README badges only when they are maintained:**
   ```markdown
   [![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Compatible-blue)](https://agentskills.io)
   [![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-green)](https://code.claude.com)
   [![Codex CLI](https://img.shields.io/badge/Codex%20CLI-Compatible-green)](https://developers.openai.com/codex)
   ```

4. **Push Updates:**
   ```bash
   git add .
   git commit -m "docs: refresh distribution metadata"
   git push
   ```

### Phase 2: Marketplace Submissions (2-3 days)

1. **Wait for Automatic Indexing:**
   - SkillsMP will auto-index within 24-48 hours
   - SkillHub will auto-index your repo
   - No action needed except GitHub topics

2. **Submit to Anthropic Official Repo:**
   - Fork [github.com/anthropics/skills](https://github.com/anthropics/skills)
   - Choose 3-5 best skills to submit initially:
     - `bio-logic` (universal reasoning skill)
     - `scientific-writing` (manuscript generation)
     - `beautiful-data-viz` (publication figures)
     - `notebooks` (marimo-first notebooks; Jupyter supported)
     - `bio-reads-qc-mapping` (sequencing data QC)
   - Add to `skills/` directory
   - Submit pull request with description
   - Reference your full repository for more skills

3. **Submit to OpenAI Codex:**
   - Fork [github.com/openai/skills](https://github.com/openai/skills)
   - Add 2-3 representative skills
   - Submit pull request

4. **Submit to MCP Market:**
   - Visit [mcpmarket.com](https://mcpmarket.com)
   - Submit repository URL
   - Add descriptions and categories

### Phase 3: Community Outreach (1 week)

1. **Awesome Lists:**
   - Submit to awesome-claude-skills
   - Create specialized awesome-bioinformatics-ai-skills?

2. **Social/Community:**
   - Reddit announcement (r/ClaudeAI, r/Bioinformatics)
   - Anthropic Discord announcement
   - Bioinformatics Slack/Discord groups
   - Twitter/X announcement with hashtags:
     ```
     #ClaudeCode #AgentSkills #Bioinformatics #ComputationalBiology
     ```

3. **Blog Post/Article:**
   - Write about creating comprehensive skill collection
   - Share on Medium, Dev.to, or your blog
   - Technical walkthrough of skill development
   - Use case examples

### Phase 4: Ongoing Maintenance

1. **Monitor Issues:**
   - Watch for GitHub issues
   - Respond to user questions
   - Accept community contributions

2. **Update Skills:**
   - Keep skills current with tool updates
   - Add new skills based on user requests
   - Improve documentation based on feedback

3. **Track Adoption:**
   - GitHub stars/forks
   - Clone counts (if visible)
   - User feedback and issues

---

## Submission Templates

## Release Process

Use GitHub Releases as the canonical release-note surface. Do not keep a
separate root `CHANGELOG.md` unless the project later needs generated
offline release history.

For each release:

1. Choose a semantic version tag such as `v1.0.0`.
2. Add human-written release notes at `.github/releases/vX.Y.Z.md`.
3. Commit and push the release-ready docs, skills, agents, catalog, and tests.
4. Create an annotated tag from the pushed commit.
5. Push the tag. `.github/workflows/release.yml` publishes the GitHub Release
   from `.github/releases/<tag>.md`.

Release notes should cover:
   - major user-facing changes
   - agent and skill coverage
   - installation or compatibility notes
   - validation commands run before release
6. Keep the README version badge pointed at the repository releases page.

### Pull Request Template (for Anthropic/OpenAI repos)

```markdown
## Skill Submission: [Skill Name]

**Description:** [One-line description]

**Domain:** Bioinformatics / Scientific Writing / Data Visualization

**Use Cases:**
- [Use case 1]
- [Use case 2]

**Tested With:**
- Claude Code: ✓
- Codex CLI: ✓

**Additional Notes:**
This skill is part of the omics-skills collection available at:
https://github.com/fmschulz/omics-skills

The collection includes 35 specialized skills and 4 expert agents for
computational biology workflows.
```

### Reddit Announcement Template

```markdown
Title: [Release] Omics Skills - Agent Skills for Bioinformatics with Claude Code/Codex

I've created a comprehensive collection of Agent Skills for computational biology:

**What it includes:**
- 4 expert agents (omics-scientist, literature-expert, science-writer, dataviz-artist)
- 35 specialized skills (reads QC, assembly, annotation, phylogenomics, literature, writing, visualization, etc.)
- Complete installation system (one-command install)
- Works with Claude Code and Codex CLI

**Use cases:**
- Genome/metagenome assembly and annotation
- Scientific manuscript writing with literature search
- Publication-quality data visualization

**Repository:** https://github.com/fmschulz/omics-skills

**Installation:**
```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
```

Feedback and contributions welcome!
```

---

## Expected Outcomes

### Short-term (1-2 weeks)
- Automatic indexing by SkillsMP and SkillHub
- GitHub stars and community interest
- Initial user feedback

### Medium-term (1-2 months)
- Official repo acceptance (Anthropic/OpenAI)
- Integration with Claude Code plugin marketplace
- Community contributions

### Long-term (3-6 months)
- Established as go-to bioinformatics skills collection
- Multiple contributors
- Adoption in academic/research settings

---

## Marketing Points

**Unique Value Propositions:**

1. **First Comprehensive Bioinformatics Collection**
   - No other skill repository covers end-to-end omics workflows
   - From raw reads to publication-ready figures

2. **Three Expert Agents**
   - Not just skills - complete agent personas that orchestrate workflows
   - Clear separation: omics-scientist, science-writer, dataviz-artist

3. **Production-Ready**
   - Battle-tested structure
   - Comprehensive documentation
   - Installation system included
   - Quality gates and validation

4. **Cross-Platform**
   - Claude Code
   - Codex CLI
   - Follows Agent Skills open standard

5. **Academic/Research Focus**
   - Literature-backed (summaries/ directories with papers)
   - Best practices from scientific community
   - Reproducibility emphasis

---

## Resources

### Official Documentation
- [Agent Skills Specification](https://agentskills.io/specification)
- [Anthropic Skills GitHub](https://github.com/anthropics/skills)
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills)
- [Agent Skills Blog Post](https://claude.com/blog/skills)

### Community Resources
- [SkillsMP Marketplace](https://skillsmp.com)
- [SkillHub](https://www.skillhub.club/)
- [MCP Market](https://mcpmarket.com)
- [awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)

### Tools
- [agent-skills-cli](https://github.com/Karanjot786/agent-skills-cli) - Universal CLI for syncing skills

---

## Questions to Consider

1. **Licensing:** Choose appropriate license (MIT, Apache 2.0, GPL)
2. **Contribution Guidelines:** Accept external contributions?
3. **Maintenance:** Who maintains? How often update?
4. **Versioning:** Use semantic versioning for skills?
5. **Support:** How to provide user support? (GitHub issues, Discord, etc.)

---

## Next Steps Checklist

- [ ] Add GitHub topics to repository
- [ ] Confirm root LICENSE file is current
- [ ] Refresh README badges only if they remain accurate
- [ ] Push updates to GitHub
- [ ] Wait for auto-indexing (SkillsMP, SkillHub)
- [ ] Submit to Anthropic skills repository
- [ ] Submit to OpenAI Codex skills
- [ ] Submit to MCP Market
- [ ] Post announcement on Reddit
- [ ] Share on Twitter/X
- [ ] Submit to awesome-claude-skills lists
- [ ] Write blog post/article
- [ ] Monitor and respond to feedback

---

Keep this page current when the agent or skill counts change.
