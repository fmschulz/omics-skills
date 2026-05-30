from __future__ import annotations

import importlib.util
import contextlib
import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


download_img_genomes = load_module(
    "download_img_genomes",
    REPO_ROOT / "skills" / "jgi-lakehouse" / "scripts" / "download_img_genomes.py",
)
rest_client = load_module(
    "jgi_rest_client",
    REPO_ROOT / "skills" / "jgi-lakehouse" / "scripts" / "rest_client.py",
)


class JgiDownloadHelperTests(unittest.TestCase):
    def test_find_genomes_rejects_untrusted_domain_before_query(self) -> None:
        with patch.object(download_img_genomes, "query") as query:
            with self.assertRaises(ValueError):
                download_img_genomes.find_genomes("Bacteria'; DROP TABLE taxon; --")
            query.assert_not_called()

    def test_find_genomes_validates_limit_before_query(self) -> None:
        with patch.object(download_img_genomes, "query") as query:
            with self.assertRaises(ValueError):
                download_img_genomes.find_genomes("Bacteria", limit=0)
            query.assert_not_called()

    def test_safe_extract_tar_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            archive = tmp / "unsafe.tar.gz"
            outside = tmp / "evil.txt"

            data = b"unsafe"
            info = tarfile.TarInfo("../evil.txt")
            info.size = len(data)
            with tarfile.open(archive, "w:gz") as tar:
                tar.addfile(info, io.BytesIO(data))

            with tarfile.open(archive, "r:gz") as tar:
                with self.assertRaises(ValueError):
                    download_img_genomes.safe_extract_tar(tar, tmp / "extract")

            self.assertFalse(outside.exists())

    def test_verify_tls_defaults_to_true_and_has_explicit_opt_out(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(download_img_genomes.verify_tls())
            self.assertTrue(rest_client.verify_tls())
        with patch.dict(os.environ, {"DREMIO_VERIFY_TLS": "false"}, clear=True):
            self.assertFalse(download_img_genomes.verify_tls())
            self.assertFalse(rest_client.verify_tls())

    def test_count_argument_reports_clean_argparse_error(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as error:
                download_img_genomes.main(["--count", "0"])
        self.assertEqual(error.exception.code, 2)
        self.assertIn("limit must be between", stderr.getvalue())


class JgiRestClientTests(unittest.TestCase):
    def test_request_options_include_tls_and_timeout(self) -> None:
        with patch.dict(os.environ, {"DREMIO_VERIFY_TLS": "0"}, clear=True):
            options = rest_client.request_options()
        self.assertEqual(options["verify"], False)
        self.assertIn("timeout", options)

    def test_cli_does_not_print_token_prefix(self) -> None:
        source = (REPO_ROOT / "skills" / "jgi-lakehouse" / "scripts" / "rest_client.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("token[:", source)
        self.assertIn('print("Token: configured")', source)


if __name__ == "__main__":
    unittest.main()
