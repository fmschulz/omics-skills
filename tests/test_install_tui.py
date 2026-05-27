import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install_tui.py"
SPEC = importlib.util.spec_from_file_location("install_tui", MODULE_PATH)
install_tui = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = install_tui
SPEC.loader.exec_module(install_tui)


class InstallTuiTests(unittest.TestCase):
    def test_initial_selection_has_all_components_checked(self):
        selection = install_tui.make_initial_selection(
            ["omics-scientist.md", "science-writer.md"],
            ["bio-logic", "scientific-writing"],
        )

        self.assertTrue(selection.all_selected)
        self.assertEqual(
            selection.selected_agents(),
            ["omics-scientist.md", "science-writer.md"],
        )
        self.assertEqual(selection.selected_skills(), ["bio-logic", "scientific-writing"])

    def test_toggle_all_clears_and_restores_every_component(self):
        selection = install_tui.make_initial_selection(
            ["omics-scientist.md", "science-writer.md"],
            ["bio-logic", "scientific-writing"],
        )

        install_tui.toggle_selection(selection, "all")
        self.assertFalse(selection.has_any)
        self.assertEqual(selection.selected_agents(), [])
        self.assertEqual(selection.selected_skills(), [])

        install_tui.toggle_selection(selection, "all")
        self.assertTrue(selection.all_selected)

    def test_toggling_one_component_unsets_all_selection(self):
        selection = install_tui.make_initial_selection(
            ["omics-scientist.md", "science-writer.md"],
            ["bio-logic", "scientific-writing"],
        )

        install_tui.toggle_selection(selection, "science-writer.md")
        install_tui.toggle_selection(selection, "skill:scientific-writing")

        self.assertFalse(selection.all_selected)
        self.assertEqual(selection.selected_agents(), ["omics-scientist.md"])
        self.assertEqual(selection.selected_skills(), ["bio-logic"])

    def test_make_install_command_encodes_selected_components(self):
        selection = install_tui.make_initial_selection(
            ["omics-scientist.md", "science-writer.md"],
            ["bio-logic", "scientific-writing"],
        )
        install_tui.toggle_selection(selection, "science-writer.md")
        install_tui.toggle_selection(selection, "skill:scientific-writing")

        self.assertEqual(
            install_tui.make_install_command("make", "copy", "1", selection),
            [
                "make",
                "--no-print-directory",
                "install-selected",
                "SELECTED_AGENT_FILES=omics-scientist.md",
                "SELECTED_SKILL_DIRS=bio-logic",
                "INSTALL_METHOD=copy",
                "VERBOSE=1",
            ],
        )

    def test_selectable_indexes_skip_headers(self):
        rows = install_tui.make_rows(["omics-scientist.md"], ["bio-logic"])

        self.assertEqual(install_tui.selectable_indexes(rows), [0, 2, 4])


if __name__ == "__main__":
    unittest.main()
