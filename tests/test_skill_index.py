from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import skill_index  # noqa: E402


class SkillIndexTests(unittest.TestCase):
    def test_parse_frontmatter_supports_folded_description(self) -> None:
        frontmatter = skill_index.parse_frontmatter(
            textwrap.dedent(
                """\
                name: example-skill
                description: >-
                  first line
                  second line
                """
            )
        )
        self.assertEqual(frontmatter["description"], "first line second line")

    def test_build_outputs_produces_expected_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skills" / "read-qc").mkdir(parents=True)
            (root / "skills" / "assembly").mkdir(parents=True)
            (root / "agents").mkdir(parents=True)

            (root / "skills" / "read-qc" / "SKILL.md").write_text(
                "---\nname: read-qc\ndescription: Quality control for reads.\n---\n# Read QC\n",
                encoding="utf-8",
            )
            (root / "skills" / "assembly" / "SKILL.md").write_text(
                "---\nname: assembly\ndescription: Assemble reads into contigs.\n---\n# Assembly\nUse /read-qc before running assembly.\n",
                encoding="utf-8",
            )
            (root / "agents" / "omics.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: omics
                    description: omics agent
                    ---
                    ## Mandatory Skill Usage

                    ### Reads
                    - `/read-qc` - quality control
                    - `/assembly` - assembly

                    ## Workflow Decision Tree

                    ```
                    START
                      └─> /read-qc
                          └─> /assembly
                    ```

                    ## Task Recognition Patterns

                    - **"reads", "qc"** → `/read-qc`
                    - **"assembly", "contigs"** → `/assembly`
                    """
                ),
                encoding="utf-8",
            )

            payload = skill_index.build_outputs(root)
            relationships = {
                (edge["source"], edge["target"], edge["type"])
                for edge in payload["relationships"]
            }
            self.assertIn(("assembly", "read-qc", "depend_on"), relationships)
            self.assertIn(("assembly", "read-qc", "compose_with"), relationships)

    def test_parse_workflow_edges_skips_sibling_branches(self) -> None:
        markdown = textwrap.dedent(
            """\
            ## Workflow Decision Tree

            ```
            START
              ├─ Need Notebook? → /notebook
              │   └─ Validation? → /notebook
              ├─ Need Figure? → /figure
              └─ Need Dashboard? → /dashboard
            ```
            """
        )
        edges = skill_index.parse_workflow_edges(markdown)
        edge_set = {(edge.source, edge.target) for edge in edges}
        self.assertNotIn(("figure", "dashboard"), edge_set)
        self.assertNotIn(("notebook", "notebook"), edge_set)

    def test_route_request_prefers_expected_agent_and_skills(self) -> None:
        result = skill_index.route_request(
            task="assemble a metagenome and recover MAGs",
            agent="omics-scientist",
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertEqual(result["agent"], "omics-scientist")
        self.assertIn("bio-assembly-qc", result["primary_skills"])
        self.assertIn("bio-binning-qc", result["primary_skills"])
        self.assertIn("bio-reads-qc-mapping", result["ordered_skills"])

    def test_route_request_uses_installed_paths_when_running_from_installed_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            home = root / "home"
            repo = root / "repo"
            index_root = home / ".agents" / "omics-skills"
            skills_root = home / ".agents" / "skills"
            codex_agents = home / ".codex" / "agents"

            (repo / "skills" / "read-qc").mkdir(parents=True)
            (repo / "skills" / "assembly").mkdir(parents=True)
            (repo / "agents").mkdir(parents=True)
            (skills_root / "read-qc").mkdir(parents=True)
            (skills_root / "assembly").mkdir(parents=True)
            codex_agents.mkdir(parents=True)
            index_root.mkdir(parents=True)

            (repo / "skills" / "read-qc" / "SKILL.md").write_text(
                "---\nname: read-qc\ndescription: read qc\n---\n# Read QC\n",
                encoding="utf-8",
            )
            (repo / "skills" / "assembly" / "SKILL.md").write_text(
                "---\nname: assembly\ndescription: assemble reads\n---\n# Assembly\nUse /read-qc before running assembly.\n",
                encoding="utf-8",
            )
            (repo / "agents" / "omics-scientist.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: omics-scientist
                    description: omics
                    ---
                    ## Mandatory Skill Usage

                    ### Reads
                    - `/read-qc` - qc
                    - `/assembly` - assembly

                    ## Workflow Decision Tree

                    ```
                    START
                      └─> /read-qc
                          └─> /assembly
                    ```

                    ## Task Recognition Patterns
                    - **"assemble", "reads"** → `/assembly`
                    """
                ),
                encoding="utf-8",
            )
            (skills_root / "read-qc" / "SKILL.md").write_text("# installed\n", encoding="utf-8")
            (skills_root / "assembly" / "SKILL.md").write_text("# installed\n", encoding="utf-8")
            (codex_agents / "omics-scientist.md").write_text("# installed agent\n", encoding="utf-8")
            (index_root / "skill_index.py").write_text("# marker\n", encoding="utf-8")

            payload = skill_index.build_outputs(repo)
            skill_index.write_outputs(payload, index_root)

            with patch.object(skill_index.Path, "home", return_value=home):
                result = skill_index.route_request(
                    task="assemble reads",
                    agent="omics-scientist",
                    platform="codex",
                    top_k=2,
                    repo=None,
                    index_root=str(index_root),
                )

            self.assertEqual(
                result["agent_path"],
                str(codex_agents / "omics-scientist.md"),
            )
            self.assertEqual(
                result["skill_paths"]["assembly"],
                str(skills_root / "assembly" / "SKILL.md"),
            )

    def test_prompt_guidance_uses_catalog_wrapper(self) -> None:
        agents_md = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/skill_index.py route", agents_md)

        for agent_name in (
            "omics-scientist.md",
            "literature-expert.md",
            "science-writer.md",
            "dataviz-artist.md",
            "codexloop.md",
        ):
            text = (REPO_ROOT / "agents" / agent_name).read_text(encoding="utf-8")
            self.assertIn("## Skill Lookup", text)
            self.assertIn("skill_index.py route", text)

    def test_literature_expert_routes_biology_preprints_to_biorxiv(self) -> None:
        result = skill_index.route_request(
            task="recent biology preprints about single cell atlases",
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertEqual(result["agent"], "literature-expert")
        self.assertIn("biorxiv-search", result["primary_skills"])

    def test_literature_expert_routes_crossref_queries_to_crossref_lookup(self) -> None:
        result = skill_index.route_request(
            task="crossref DOI lookup for citation metadata",
            agent="literature-expert",
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertIn("crossref-lookup", result["primary_skills"])

    def test_literature_expert_routes_impact_queries_to_scientific_impact_assessment(self) -> None:
        result = skill_index.route_request(
            task="compare papers by citation count altmetric and impact factor",
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertEqual(result["agent"], "literature-expert")
        self.assertIn("scientific-impact-assessment", result["primary_skills"])


if __name__ == "__main__":
    unittest.main()
