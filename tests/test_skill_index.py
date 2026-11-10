from __future__ import annotations

import contextlib
import io
import json
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

    def test_incidental_runtime_mention_does_not_restrict_skill_platforms(self) -> None:
        self.assertEqual(skill_index.extract_platforms(""), ["claude", "codex"])
        self.assertEqual(
            skill_index.extract_platforms("[codex]"),
            ["codex"],
        )
        payload = skill_index.build_outputs(REPO_ROOT)
        evaluator = next(
            skill
            for skill in payload["catalog"]["skills"]
            if skill["name"] == "ai-scientist-evaluator"
        )
        self.assertEqual(evaluator["platforms"], ["claude", "codex"])

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
                    ## Skills

                    | Skill | Use for | Phrases | After |
                    | --- | --- | --- | --- |
                    | `read-qc` | Reads | "reads", "qc" | |
                    | `assembly` | Assembly | "assembly", "contigs" | `read-qc` |
                    """
                ),
                encoding="utf-8",
            )

            payload = skill_index.build_outputs(root)
            relationships = {
                (edge["source"], edge["target"], edge["type"])
                for edge in payload["catalog"]["edges"]
                if edge["source_type"] == "skill" and edge["target_type"] == "skill"
            }
            self.assertIn(("read-qc", "assembly", "workflow_next"), relationships)
            self.assertIn(("assembly", "read-qc", "depend_on"), relationships)
            self.assertIn(("assembly", "read-qc", "compose_with"), relationships)
            agent_edges = {
                (edge["source"], edge["target"], edge["type"])
                for edge in payload["catalog"]["edges"]
                if edge["source_type"] == "agent"
            }
            self.assertEqual(
                agent_edges,
                {("omics", "read-qc", "uses"), ("omics", "assembly", "uses")},
            )
            agent = payload["catalog"]["agents"][0]
            self.assertEqual(
                agent["skill_sections"],
                {"Assembly": ["assembly"], "Reads": ["read-qc"]},
            )
            self.assertEqual(
                agent["task_patterns"],
                [
                    {"skill_name": "read-qc", "phrases": ["reads", "qc"]},
                    {"skill_name": "assembly", "phrases": ["assembly", "contigs"]},
                ],
            )

    def test_parse_agent_table_reads_label_phrases_and_prerequisites(self) -> None:
        markdown = textwrap.dedent(
            """\
            ## Skills

            | Skill | Use for | Phrases | After |
            | --- | --- | --- | --- |
            | `notebooks` | Notebook authoring | "marimo", "notebook" | |
            | `dashboard` | Dashboards | "dashboard" | `notebooks`, `figure` |
            """
        )
        rows = skill_index.parse_agent_table(markdown)
        self.assertEqual(
            rows,
            [
                skill_index.AgentSkillRow(
                    "notebooks", "Notebook authoring", ["marimo", "notebook"], []
                ),
                skill_index.AgentSkillRow(
                    "dashboard", "Dashboards", ["dashboard"], ["notebooks", "figure"]
                ),
            ],
        )

    def test_parse_agent_table_ignores_prose_and_other_sections(self) -> None:
        markdown = textwrap.dedent(
            """\
            Send prose to `academic-writing` with `stop-slop`.

            ## Prose

            | Skill | Use for | Phrases | After |
            | --- | --- | --- | --- |
            | `not-a-skill-row` | Prose | "prose" | |

            ## Skills

            | Skill | Use for |
            | --- | --- |
            | `bio-logic` | Evidence checks |

            Review goes to `nelli-paper-review`.
            """
        )
        rows = skill_index.parse_agent_table(markdown)
        self.assertEqual(
            rows, [skill_index.AgentSkillRow("bio-logic", "Evidence checks", [], [])]
        )

    def test_parse_agent_table_without_a_skills_section_is_empty(self) -> None:
        self.assertEqual(skill_index.parse_agent_table("## Principles\n\ntext\n"), [])

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
        self.assertEqual(result["primary_skills"][0], "omics-pipeline")
        self.assertIn("bio-assembly-qc", result["primary_skills"])
        self.assertIn("bio-binning-qc", result["primary_skills"])
        self.assertIn("bio-reads-qc-mapping", result["ordered_skills"])
        self.assertEqual(result["ordered_skills"][0], "omics-pipeline")
        self.assertIn("bio-assembly-qc", result["hidden_skills"])
        self.assertNotIn("omics-pipeline", result["hidden_skills"])

    def test_pull_reads_from_data_repository_routes_to_read_qc(self) -> None:
        result = skill_index.route_request(
            task="pull raw sequencing reads from a public data repository and run quality control",
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertIn("bio-reads-qc-mapping", result["primary_skills"])

    def test_figure_out_heatmap_routes_to_visualization(self) -> None:
        result = skill_index.route_request(
            task="help me figure out a heatmap",
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertIn("beautiful-data-viz", result["primary_skills"])

    def test_omics_skills_repo_audit_is_a_hard_negative(self) -> None:
        result = skill_index.route_request(
            task=(
                "go over this omics-skills repo, diagnose bugs, improve the "
                "skill setup, and improve the writeup"
            ),
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertEqual(result["primary_skills"], [])
        self.assertEqual(result["ordered_skills"], [])

    def test_generic_single_token_pattern_overlap_is_suppressed(self) -> None:
        query_tokens = skill_index.tokenize("perform a code review of this repository")
        self.assertEqual(
            skill_index.task_pattern_overlap(query_tokens, skill_index.tokenize("peer review")),
            0.0,
        )
        self.assertGreater(
            skill_index.task_pattern_overlap(query_tokens, skill_index.tokenize("code review")),
            0.0,
        )

    def test_multi_token_pattern_requires_two_tokens_and_one_distinctive_token(self) -> None:
        self.assertEqual(
            skill_index.task_pattern_overlap(
                skill_index.tokenize("help me write a paper"),
                skill_index.tokenize("paper to markdown"),
            ),
            0.0,
        )
        self.assertEqual(
            skill_index.task_pattern_overlap(
                skill_index.tokenize("review this pull request"),
                skill_index.tokenize("review this manuscript"),
            ),
            0.0,
        )
        self.assertGreater(
            skill_index.task_pattern_overlap(
                skill_index.tokenize("convert paper to markdown"),
                skill_index.tokenize("paper to markdown"),
            ),
            0.0,
        )

    def test_task_phrases_match_word_boundaries_and_skip_figure_out(self) -> None:
        self.assertFalse(skill_index.phrase_matches("I need a treemap", "tree"))
        self.assertFalse(skill_index.phrase_matches("help me figure out a threshold", "figure"))
        self.assertTrue(
            skill_index.phrase_matches(
                "figure out how to revise this figure",
                "figure",
            )
        )
        self.assertTrue(skill_index.phrase_matches("build a phylogenetic tree", "tree"))

    def test_generic_gene_does_not_activate_hgt_pattern(self) -> None:
        query_tokens = skill_index.tokenize("build a phylogenetic tree from marker gene alignments")
        self.assertEqual(
            skill_index.task_pattern_overlap(
                query_tokens,
                skill_index.tokenize("gene donor"),
            ),
            0.0,
        )

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
                    ## Skills

                    | Skill | Use for | Phrases | After |
                    | --- | --- | --- | --- |
                    | `read-qc` | Reads | "qc" | |
                    | `assembly` | Assembly | "assemble", "reads" | `read-qc` |
                    """
                ),
                encoding="utf-8",
            )
            (skills_root / "read-qc" / "SKILL.md").write_text("# installed\n", encoding="utf-8")
            (skills_root / "assembly" / "SKILL.md").write_text("# installed\n", encoding="utf-8")
            (codex_agents / "omics-scientist.toml").write_text(
                'name = "omics-scientist"\n', encoding="utf-8"
            )
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
                str(codex_agents / "omics-scientist.toml"),
            )
            self.assertEqual(
                result["skill_paths"]["assembly"],
                str(skills_root / "assembly" / "SKILL.md"),
            )

    def test_filter_catalog_payload_removes_unselected_agents_and_skills(self) -> None:
        payload = skill_index.build_outputs(REPO_ROOT)
        filtered = skill_index.filter_catalog_payload(
            payload,
            include_agents=["science-writer.md"],
            include_skills=["bio-logic", "proposal-review"],
        )
        catalog = filtered["catalog"]
        self.assertEqual([agent["name"] for agent in catalog["agents"]], ["science-writer"])
        self.assertEqual(
            [skill["name"] for skill in catalog["skills"]],
            ["bio-logic", "proposal-review"],
        )
        for agent in catalog["agents"]:
            for section_skills in agent["skill_sections"].values():
                self.assertLessEqual(
                    set(section_skills), {"bio-logic", "proposal-review"}
                )
            for pattern in agent["task_patterns"]:
                self.assertIn(pattern["skill_name"], {"bio-logic", "proposal-review"})
        for edge in catalog["edges"]:
            if edge["source_type"] == "agent":
                self.assertEqual(edge["source"], "science-writer")
                self.assertIn(edge["target"], {"bio-logic", "proposal-review"})
            if edge["source_type"] == "skill":
                self.assertIn(edge["source"], {"bio-logic", "proposal-review"})
                self.assertIn(edge["target"], {"bio-logic", "proposal-review"})

    def test_filter_catalog_payload_supports_skills_only_install(self) -> None:
        payload = skill_index.build_outputs(REPO_ROOT)
        filtered = skill_index.filter_catalog_payload(
            payload,
            include_agents=["__none__"],
            include_skills=["proposal-review"],
        )
        catalog = filtered["catalog"]
        self.assertEqual(catalog["agents"], [])
        self.assertEqual(
            [skill["name"] for skill in catalog["skills"]], ["proposal-review"]
        )
        self.assertEqual(catalog["metadata"]["agent_count"], 0)
        self.assertEqual(catalog["metadata"]["skill_count"], 1)
        self.assertFalse(
            any(edge["source_type"] == "agent" or edge.get("target_type") == "agent" for edge in catalog["edges"])
        )

    def test_prompt_guidance_uses_catalog_wrapper(self) -> None:
        agents_md = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/skill_index.py route", agents_md)

        for agent_name in (
            "omics-scientist.md",
            "literature-expert.md",
            "science-writer.md",
        ):
            text = (REPO_ROOT / "agents" / agent_name).read_text(encoding="utf-8")
            self.assertIn("## Skill Lookup", text)
            self.assertIn("skill_index.py route", text)

    def test_literature_expert_routes_biology_preprints_to_preprint_search(
        self,
    ) -> None:
        result = skill_index.route_request(
            task="recent biology preprints about single cell atlases",
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertEqual(result["agent"], "literature-expert")
        self.assertIn("preprint-search", result["primary_skills"])

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

    def test_literature_expert_routes_impact_queries_to_crossref_lookup(self) -> None:
        result = skill_index.route_request(
            task="compare papers by citation count altmetric and impact factor",
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertEqual(result["agent"], "literature-expert")
        self.assertIn("crossref-lookup", result["primary_skills"])


class SkillRefPatternTests(unittest.TestCase):
    """Guard tests for SKILL_REF_PATTERN so prose like matplotlib/seaborn,
    docs/plans, DOI/date-range, https://github.com/... stops being parsed as
    phantom skill references."""

    def _find(self, text: str) -> list[str]:
        return skill_index.SKILL_REF_PATTERN.findall(text)

    def test_ignores_intra_word_slashes(self) -> None:
        self.assertEqual(self._find("matplotlib/seaborn"), [])
        self.assertEqual(self._find("docs/plans"), [])
        self.assertEqual(self._find("completeness/contamination"), [])
        self.assertEqual(self._find("genome/metagenome"), [])
        self.assertEqual(self._find("DOI/date-range"), [])

    def test_ignores_url_and_path_slashes(self) -> None:
        self.assertEqual(self._find("https://example.com/foo"), [])
        self.assertEqual(self._find("file:///etc/passwd"), [])
        self.assertEqual(self._find("./coastal-metagenomes ../shared-data"), [])
        self.assertEqual(self._find("// comment with /bar-baz inside"), ["bar-baz"])

    def test_matches_valid_skill_refs(self) -> None:
        self.assertEqual(self._find("Use /bio-annotation after QC"), ["bio-annotation"])
        self.assertEqual(
            self._find("- `/proposal-review` - funding review"), ["proposal-review"]
        )
        self.assertEqual(self._find("(/bio-annotation)"), ["bio-annotation"])
        self.assertEqual(self._find("/notebooks at line start"), ["notebooks"])


class CatalogConsistencyTests(unittest.TestCase):
    """Integration tests that hold the shipped repo state consistent. They
    run against the real skills/ and agents/ directories — not fixtures —
    so they fail on any drift between SKILL.md files, agent Mandatory Skill
    Usage sections, and directory layout."""

    def test_every_skill_dir_has_skill_md_and_name_matches(self) -> None:
        skills_root = REPO_ROOT / "skills"
        for entry in sorted(skills_root.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            self.assertTrue(
                skill_md.exists(),
                f"{entry.name} is a skills/ subdirectory with no SKILL.md",
            )
            frontmatter, _ = skill_index.split_frontmatter(skill_md.read_text(encoding="utf-8"))
            self.assertEqual(
                frontmatter.get("name"),
                entry.name,
                f"{entry.name}/SKILL.md has frontmatter name={frontmatter.get('name')!r} "
                f"but directory is {entry.name!r}",
            )

    def test_skills_root_has_no_stray_files(self) -> None:
        skills_root = REPO_ROOT / "skills"
        stray = [entry.name for entry in skills_root.iterdir() if entry.is_file()]
        self.assertEqual(
            stray, [], f"skills/ root contains non-directory entries: {stray}"
        )

    def test_no_nested_duplicate_skill_dirs(self) -> None:
        """A skills/<name>/<name>/ nested copy almost always means an
        accidentally-duplicated skill tree. Fail loudly if any appear."""
        skills_root = REPO_ROOT / "skills"
        duplicates = []
        for entry in skills_root.iterdir():
            if not entry.is_dir():
                continue
            nested = entry / entry.name
            if nested.is_dir():
                duplicates.append(str(nested.relative_to(REPO_ROOT)))
        self.assertEqual(
            duplicates, [], f"Nested duplicate skill directories detected: {duplicates}"
        )

    def test_agent_skill_references_all_resolve(self) -> None:
        """Every skill in an agent's `## Skills` table, in its Phrases and in its
        After column, must resolve to a real skill. Phantoms here mean the
        routing layer will propose a skill that doesn't exist."""
        unresolved = [
            item
            for item in skill_index.collect_unresolved_references(REPO_ROOT)
            if item[0] in {"agent", "agent_task_pattern", "workflow_edge"}
        ]
        self.assertEqual(
            unresolved,
            [],
            f"Unresolved agent-side skill references: {unresolved}",
        )

    def test_catalog_agents_only_reference_real_skills(self) -> None:
        """catalog.agents[].skill_sections and task_patterns must only reference
        skills that exist in catalog.skills. This is the belt-and-suspenders
        filter that protects downstream consumers from phantom skill names."""
        payload = skill_index.build_outputs(REPO_ROOT)
        real = {skill["name"] for skill in payload["catalog"]["skills"]}
        for agent in payload["catalog"]["agents"]:
            for section_skills in agent["skill_sections"].values():
                for skill_name in section_skills:
                    self.assertIn(
                        skill_name,
                        real,
                        f"catalog.agents[{agent['name']!r}].skill_sections contains "
                        f"{skill_name!r}, which is not in catalog.skills",
                    )
            for pattern in agent["task_patterns"]:
                self.assertIn(
                    pattern["skill_name"],
                    real,
                    f"catalog.agents[{agent['name']!r}].task_patterns references "
                    f"{pattern['skill_name']!r}, which is not in catalog.skills",
                )

    def test_every_shipped_agent_has_a_skill_table(self) -> None:
        payload = skill_index.build_outputs(REPO_ROOT)
        for agent in payload["catalog"]["agents"]:
            self.assertTrue(
                agent["skill_sections"],
                f"agents/{agent['name']}.md has no rows in its `## Skills` table",
            )

    def test_no_agent_phrase_is_a_bare_generic_word(self) -> None:
        """A bare "write" or "review" phrase would pull unrelated requests (a
        README, a pull request) into a science skill."""
        payload = skill_index.build_outputs(REPO_ROOT)
        for agent in payload["catalog"]["agents"]:
            for pattern in agent["task_patterns"]:
                generic = set(pattern["phrases"]) & skill_index.WEAK_PATTERN_TOKENS
                self.assertEqual(
                    generic,
                    set(),
                    f"{agent['name']}: {pattern['skill_name']} has generic phrases",
                )

    def test_every_skill_is_owned_by_an_agent(self) -> None:
        """A skill that no agent lists cannot be routed to, hidden stages included."""
        payload = skill_index.build_outputs(REPO_ROOT)
        unowned = [
            skill["name"]
            for skill in payload["catalog"]["skills"]
            if not skill["agents"]
        ]
        self.assertEqual(
            unowned, [], f"skills in no agent's `## Skills` table: {unowned}"
        )

    def test_catalog_hidden_flag_matches_the_frontmatter(self) -> None:
        payload = skill_index.build_outputs(REPO_ROOT)
        for skill in payload["catalog"]["skills"]:
            text = (REPO_ROOT / skill["path"]).read_text(encoding="utf-8")
            frontmatter, _ = skill_index.split_frontmatter(text)
            self.assertEqual(
                skill["hidden"],
                frontmatter.get("disable-model-invocation") == "true",
                skill["name"],
            )


class HiddenStageRoutingTests(unittest.TestCase):
    """Hidden stage skills are not listed to the model, so a route to one must
    name the `omics-pipeline` router first and mark the stage as hidden."""

    def _write_repo(self, root: Path) -> None:
        skills = {
            "omics-pipeline": ("Route omics pipeline work to its stage skill.", ""),
            "stage-qc": (
                "Quality control for sequencing reads.",
                "disable-model-invocation: true\n",
            ),
            "stage-map": (
                "Align contigs onto assemblies.",
                "disable-model-invocation: true\n",
            ),
            "plain-skill": ("Convert notebooks between formats.", ""),
        }
        for name, (description, extra) in skills.items():
            (root / "skills" / name).mkdir(parents=True)
            (root / "skills" / name / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: {description}\n{extra}---\n"
                f"# {name}\n",
                encoding="utf-8",
            )
        (root / "agents").mkdir()
        (root / "agents" / "omics-scientist.md").write_text(
            textwrap.dedent(
                """\
                ---
                name: omics-scientist
                description: omics
                ---
                ## Skills

                | Skill | Use for | Phrases | After |
                | --- | --- | --- | --- |
                | `omics-pipeline` | Pipeline entry | "omics pipeline" | |
                | `stage-qc` | Reads | "sequencing reads" | |
                | `stage-map` | Mapping | "align contigs" | |
                | `plain-skill` | Notebooks | "convert notebooks" | |
                """
            ),
            encoding="utf-8",
        )

    def _route(self, root: Path, task: str, **kwargs: object) -> dict:
        return skill_index.route_request(
            task=task,
            agent=kwargs.get("agent"),
            platform="codex",
            top_k=4,
            repo=str(root),
            index_root=None,
        )

    def test_catalog_marks_hidden_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            skills = {
                s["name"]: s
                for s in skill_index.build_outputs(root)["catalog"]["skills"]
            }
            self.assertEqual(
                {name: skill["hidden"] for name, skill in skills.items()},
                {
                    "omics-pipeline": False,
                    "stage-qc": True,
                    "stage-map": True,
                    "plain-skill": False,
                },
            )

    def test_hidden_stage_route_names_the_router_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            result = self._route(root, "quality control for sequencing reads")
            self.assertEqual(result["primary_skills"], ["omics-pipeline", "stage-qc"])
            self.assertEqual(result["ordered_skills"][0], "omics-pipeline")
            self.assertEqual(result["hidden_skills"], ["stage-qc"])

    def test_visible_only_route_does_not_add_the_router(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            result = self._route(root, "convert notebooks between formats")
            self.assertEqual(result["primary_skills"], ["plain-skill"])
            self.assertEqual(result["hidden_skills"], [])

    def _skills(self, root: Path) -> dict:
        catalog = skill_index.build_outputs(root)["catalog"]
        return {skill["name"]: skill for skill in catalog["skills"]}

    def test_selecting_a_stage_adds_the_router_and_the_other_stages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            names, message = skill_index.expand_skill_selection(
                self._skills(root), ["stage-qc"]
            )
            self.assertEqual(names, ["stage-qc", "omics-pipeline", "stage-map"])
            self.assertIn("omics-pipeline", message)
            self.assertNotIn("stage-qc,", message)

    def test_expanding_an_expanded_selection_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            skills = self._skills(root)
            once, _ = skill_index.expand_skill_selection(
                skills, ["plain-skill", "stage-qc"]
            )
            twice, message = skill_index.expand_skill_selection(skills, once)
            self.assertEqual(twice, once)
            self.assertEqual(message, "")

    def test_selecting_the_router_adds_every_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            names, message = skill_index.expand_skill_selection(
                self._skills(root), ["omics-pipeline"]
            )
            self.assertEqual(names, ["omics-pipeline", "stage-map", "stage-qc"])
            self.assertIn("stage-map", message)
            self.assertIn("stage-qc", message)

    def test_a_visible_or_complete_selection_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            skills = self._skills(root)
            self.assertEqual(
                skill_index.expand_skill_selection(skills, ["plain-skill"]),
                (["plain-skill"], ""),
            )
            everything = ["omics-pipeline", "stage-qc", "stage-map"]
            self.assertEqual(
                skill_index.expand_skill_selection(skills, everything), (everything, "")
            )

    def test_expand_selection_command_prints_the_names_and_one_line_of_notice(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = skill_index.main(
                    ["expand-selection", "--repo", str(root), "plain-skill", "stage-qc"]
                )
            self.assertEqual(rc, 0)
            self.assertEqual(
                out.getvalue().split(),
                ["plain-skill", "stage-qc", "omics-pipeline", "stage-map"],
            )
            self.assertEqual(len(err.getvalue().strip().splitlines()), 1)

    def test_selected_build_includes_the_required_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            out_dir = root / "subset"
            argv = ["build", "--repo", str(root), "--out", str(out_dir)]
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                skill_index.main([*argv, "--include-skill", "stage-qc"])
            catalog = json.loads((out_dir / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [skill["name"] for skill in catalog["skills"]],
                ["omics-pipeline", "stage-map", "stage-qc"],
            )

    def test_router_is_not_added_when_the_pinned_agent_does_not_own_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_repo(root)
            (root / "agents" / "reader.md").write_text(
                "---\nname: reader\ndescription: reads\n---\n"
                "## Skills\n\n| Skill | Use for |\n| --- | --- |\n"
                "| `stage-qc` | Reads |\n",
                encoding="utf-8",
            )
            result = self._route(
                root, "quality control for sequencing reads", agent="reader"
            )
            self.assertEqual(result["primary_skills"], ["stage-qc"])


class AgentSectionHeadingScoringTests(unittest.TestCase):
    """When a skill is co-owned by multiple agents, the section heading
    each agent files it under breaks the tie. Guards against the router
    regressing to a pure-alphabetical-tiebreak on shared skills."""

    def test_section_heading_wins_over_alphabetical_tiebreak(self) -> None:
        # bio-logic is listed by omics-scientist (Use for: "Scientific reasoning
        # and hypothesis formation") and by other agents under their own
        # labels. A "hypothesis" query must route to omics-scientist even when
        # another agent wins alphabetically.
        result = skill_index.route_request(
            task="formulate a hypothesis for why certain strains outperform others",
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertIn("bio-logic", result["primary_skills"])
        self.assertEqual(result["agent"], "omics-scientist")


class AgentOwnershipFilterTests(unittest.TestCase):
    """Pinning an agent must constrain every path that can add a skill:
    scoring, compose neighbours, and dependency expansion. Dependency
    expansion used to skip the filter, so `--agent literature-expert`
    returned bio-annotation and put it first in the suggested order."""

    def test_pinned_agent_never_recommends_a_skill_it_does_not_own(self) -> None:
        payload = skill_index.build_outputs(REPO_ROOT)
        agents = {item["name"]: item for item in payload["catalog"]["agents"]}
        for agent_name in agents:
            owned = skill_index._allowed_skills_for_agent(agent_name, agents)
            for task in (
                "literature search",
                "assemble a metagenome and recover MAGs",
                "draft the discussion section",
            ):
                result = skill_index.route_request(
                    task=task,
                    agent=agent_name,
                    platform="codex",
                    top_k=4,
                    repo=str(REPO_ROOT),
                    index_root=None,
                )
                recommended = set(result["primary_skills"]) | set(result["supporting_skills"])
                recommended |= set(result["ordered_skills"])
                self.assertEqual(
                    recommended - owned,
                    set(),
                    f"{agent_name} recommended unowned skills for {task!r}",
                )


class SoftwareRepoVetoTests(unittest.TestCase):
    """The repo-review veto silences the router for code-review prompts. A
    scientific subject word must override it, or "improve the manuscript in
    this repository" returns nothing at all."""

    def test_code_review_prompts_stay_silent(self) -> None:
        for task in (
            "review this repository's code structure",
            "audit the repo installer scripts",
            "fix bugs in the codebase",
        ):
            self.assertTrue(
                skill_index.is_software_repo_review(skill_index.tokenize(task)), task
            )

    def test_scientific_subject_overrides_the_veto(self) -> None:
        for task in (
            "improve the scientific manuscript in this repository",
            "review the genome annotation in this repo",
        ):
            self.assertFalse(
                skill_index.is_software_repo_review(skill_index.tokenize(task)), task
            )


class ManuscriptProseVetoTests(unittest.TestCase):
    """The pack ships no manuscript-prose skill (academic-writing is another
    repository's), so a drafting request must route to nothing. Generating a
    Methods section from workflow run artifacts is a different request that
    bio-workflow-methods-docwriter owns."""

    def _route(self, task: str) -> dict:
        return skill_index.route_request(
            task=task,
            agent=None,
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )

    def test_manuscript_drafting_routes_to_nothing(self) -> None:
        for task in (
            "draft the methods section of a manuscript on metagenomic binning",
            "write the methods section of my paper",
            "revise the abstract of my paper on viral genomes",
            "rewrite this Discussion for clarity, keeping every claim",
        ):
            with self.subTest(task=task):
                result = self._route(task)
                self.assertEqual(result["primary_skills"], [])
                self.assertEqual(result["ordered_skills"], [])

    def test_methods_from_workflow_artifacts_still_route_to_the_docwriter(self) -> None:
        for task in (
            "generate reproducible methods documentation from a Nextflow pipeline run",
            "write the methods section from these Snakemake run artifacts",
        ):
            with self.subTest(task=task):
                result = self._route(task)
                self.assertIn(
                    "bio-workflow-methods-docwriter", result["primary_skills"]
                )

    def test_a_pinned_agent_is_not_silenced(self) -> None:
        result = skill_index.route_request(
            task="write the methods section of my paper",
            agent="omics-scientist",
            platform="codex",
            top_k=4,
            repo=str(REPO_ROOT),
            index_root=None,
        )
        self.assertIn("bio-workflow-methods-docwriter", result["primary_skills"])

    def test_prose_detection_needs_an_action_and_a_manuscript_noun(self) -> None:
        tokens = skill_index.tokenize
        self.assertTrue(
            skill_index.is_manuscript_prose_request(tokens("draft my manuscript"))
        )
        self.assertFalse(
            skill_index.is_manuscript_prose_request(tokens("edit the config section"))
        )
        self.assertFalse(
            skill_index.is_manuscript_prose_request(
                tokens("the manuscript figure data")
            )
        )
        self.assertFalse(
            skill_index.is_manuscript_prose_request(
                tokens("write the paper methods from a Nextflow run")
            )
        )


class CatalogPathPortabilityTests(unittest.TestCase):
    """Catalog JSON on disk stores repo-relative paths; route_request resolves
    them back to absolute by detecting the repo root from the catalog's own
    location (catalog.json lives at <repo>/catalog/), so a shared catalog
    resolves correctly regardless of where the repo is checked out — without
    baking the committing machine's absolute path into the file."""

    def test_catalog_paths_are_repo_relative(self) -> None:
        payload = skill_index.build_outputs(REPO_ROOT)
        for item in payload["catalog"]["skills"]:
            self.assertFalse(
                Path(item["path"]).is_absolute(),
                f"catalog.skills[{item['name']!r}].path is absolute: {item['path']!r}",
            )
            self.assertTrue(
                item["path"].startswith("skills/"),
                f"catalog.skills[{item['name']!r}].path should start with 'skills/': {item['path']!r}",
            )
        for item in payload["catalog"]["agents"]:
            self.assertFalse(Path(item["path"]).is_absolute())
            self.assertTrue(item["path"].startswith("agents/"))

    def test_catalog_metadata_is_deterministic(self) -> None:
        """The committed catalog must be byte-stable across machines and time so
        a `git diff` freshness check is meaningful: no build timestamp, no
        absolute source path, and two builds of the same repo are identical."""
        first = skill_index.build_outputs(REPO_ROOT)
        second = skill_index.build_outputs(REPO_ROOT)
        self.assertEqual(first, second)
        metadata = first["catalog"]["metadata"]
        self.assertNotIn("built_at", metadata)
        self.assertNotIn("source_repo", metadata)

    def test_route_request_resolves_relative_paths_from_catalog_location(self) -> None:
        """Write the built catalog under a repo-shaped directory's catalog/ dir.
        route_request with --index-root resolves skill paths to absolute by
        detecting the repo root from the catalog's location, with no
        metadata.source_repo needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "skills").mkdir()
            (repo / "agents").mkdir()
            index_root = repo / "catalog"
            index_root.mkdir()
            payload = skill_index.build_outputs(REPO_ROOT)
            skill_index.write_outputs(payload, index_root)
            result = skill_index.route_request(
                task="assemble a metagenome and recover MAGs",
                agent="omics-scientist",
                platform="codex",
                top_k=4,
                repo=None,
                index_root=str(index_root),
            )
            self.assertEqual(result["agent"], "omics-scientist")
            self.assertIn("bio-assembly-qc", result["primary_skills"])
            for name, path in result["skill_paths"].items():
                self.assertTrue(
                    Path(path).is_absolute(),
                    f"route_request must emit absolute paths; got {path!r} for {name!r}",
                )
                self.assertTrue(
                    path.startswith(str(repo)),
                    f"path should resolve under the catalog's repo {repo}; got {path!r}",
                )

    def test_catalog_is_checkout_portable_across_different_repo_paths(self) -> None:
        """The whole point of committing catalog/*.json is that a second
        clone at a different filesystem path still produces usable routes.
        Simulate that: build a catalog under repo A, then ship that catalog to
        repo B at a different path. route_request against repo B's catalog/ must
        resolve skill paths under repo B (via repo-root detection from the
        catalog's location), not A."""
        with tempfile.TemporaryDirectory() as a_dir, tempfile.TemporaryDirectory() as b_dir:
            a_root = Path(a_dir) / "repo_a"
            b_root = Path(b_dir) / "repo_b"
            for root in (a_root, b_root):
                (root / "skills" / "bio-assembly-qc").mkdir(parents=True)
                (root / "skills" / "bio-reads-qc-mapping").mkdir(parents=True)
                (root / "agents").mkdir(parents=True)
                (root / "catalog").mkdir(parents=True)
                (root / "skills" / "bio-assembly-qc" / "SKILL.md").write_text(
                    "---\nname: bio-assembly-qc\ndescription: Assemble genomes and metagenomes.\n---\n# Assembly\n",
                    encoding="utf-8",
                )
                (root / "skills" / "bio-reads-qc-mapping" / "SKILL.md").write_text(
                    "---\nname: bio-reads-qc-mapping\ndescription: QC and trim reads.\n---\n# Reads\nRun before /bio-assembly-qc.\n",
                    encoding="utf-8",
                )
                (root / "agents" / "omics-scientist.md").write_text(
                    "---\nname: omics-scientist\ndescription: omics\n---\n"
                    "## Skills\n\n| Skill | Use for |\n| --- | --- |\n"
                    "| `bio-reads-qc-mapping` | Pipeline |\n"
                    "| `bio-assembly-qc` | Pipeline |\n",
                    encoding="utf-8",
                )

            # Build the catalog against repo A; metadata.source_repo == a_root.
            payload = skill_index.build_outputs(a_root)
            skill_index.write_outputs(payload, b_root / "catalog")

            # Wipe repo A completely. If the catalog is portable, routing
            # against B's catalog/ still resolves under B.
            import shutil

            shutil.rmtree(a_root)

            result = skill_index.route_request(
                task="assemble a metagenome and recover MAGs",
                agent="omics-scientist",
                platform="codex",
                top_k=4,
                repo=None,
                index_root=str(b_root / "catalog"),
            )
            for name, path in result["skill_paths"].items():
                self.assertTrue(
                    path.startswith(str(b_root)),
                    f"catalog must resolve under the local checkout {b_root}, "
                    f"but {name} resolved to {path}",
                )
                self.assertTrue(
                    Path(path).exists(),
                    f"resolved path does not exist: {path!r}",
                )


class CliTests(unittest.TestCase):
    """Exercise the argparse entry point end-to-end so the CLI wiring (build +
    route subcommands, text and JSON output) stays covered."""

    def test_build_command_writes_only_catalog_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                rc = skill_index.main(["build", "--repo", str(REPO_ROOT), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue((out / "catalog.json").exists())
            # relationships.json / routing.json were removed; build must not emit them.
            self.assertFalse((out / "relationships.json").exists())
            self.assertFalse((out / "routing.json").exists())
            printed = json.loads(buffer.getvalue())
            self.assertEqual(set(printed), {"catalog"})

    def test_build_command_can_emit_selected_subset_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                rc = skill_index.main(
                    [
                        "build",
                        "--repo",
                        str(REPO_ROOT),
                        "--out",
                        str(out),
                        "--include-agent",
                        "science-writer.md",
                        "--include-skill",
                        "proposal-review",
                    ]
                )
            self.assertEqual(rc, 0)
            catalog = json.loads((out / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual([agent["name"] for agent in catalog["agents"]], ["science-writer"])
            self.assertEqual(
                [skill["name"] for skill in catalog["skills"]], ["proposal-review"]
            )

    def test_route_command_text_output(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = skill_index.main(
                ["route", "assemble a metagenome and recover MAGs", "--repo", str(REPO_ROOT)]
            )
        self.assertEqual(rc, 0)
        output = buffer.getvalue()
        self.assertIn("Agent: omics-scientist", output)
        self.assertIn("bio-assembly-qc", output)

    def test_route_command_json_output(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = skill_index.main(
                ["route", "find recent arxiv preprints", "--repo", str(REPO_ROOT), "--json"]
            )
        self.assertEqual(rc, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["agent"], "literature-expert")
        self.assertIn("preprint-search", payload["primary_skills"])


if __name__ == "__main__":
    unittest.main()
