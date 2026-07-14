import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import officecli_local_review_adapter as adapter


def write_minimal_pptx(path: Path, slide_count: int = 2) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        for index in range(1, slide_count + 1):
            archive.writestr(
                f"ppt/slides/slide{index}.xml",
                "<p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main' />",
            )


def write_minimal_png(path: Path) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    )


class OfficeCliLocalReviewAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.pptx = self.root / "deck.pptx"
        self.output = self.root / "result.json"
        self.local_output = self.root / "pages"
        self.renderer = self.root / "renderer.ps1"
        self.renderer.write_text("# test", encoding="utf-8")
        write_minimal_pptx(self.pptx, slide_count=2)

    def successful_render(self) -> subprocess.CompletedProcess[str]:
        self.local_output.mkdir(exist_ok=True)
        pages = [self.local_output / "page-1.png", self.local_output / "page-2.png"]
        for page in pages:
            write_minimal_png(page)
        response = {
            "status": "success",
            "page_count": 2,
            "pages": [str(page) for page in pages],
            "renderer": "fusion-bundled-local",
        }
        return subprocess.CompletedProcess(["powershell"], 0, json.dumps(response), "")

    def local_args(self) -> list[str]:
        return [
            "--pptx",
            str(self.pptx),
            "--local-renderer",
            str(self.renderer),
            "--local-output-dir",
            str(self.local_output),
            "--output",
            str(self.output),
        ]

    def test_bundled_renderer_is_default(self) -> None:
        with mock.patch.dict(adapter.os.environ, {}, clear=True):
            renderer = adapter.find_local_renderer(None)
        self.assertEqual(renderer, (SCRIPTS_DIR / "officecli_local_review.ps1").resolve())

    def test_bundled_renderer_contains_no_remote_service_commands(self) -> None:
        text = (SCRIPTS_DIR / "officecli_local_review.ps1").read_text(
            encoding="utf-8"
        ).lower()
        forbidden = ("officecli.exe", "officecli login", "set-key", "whoami", "publish")
        self.assertTrue(all(token not in text for token in forbidden))

    def test_local_render_prepares_evidence_without_claiming_inspection(self) -> None:
        completed = self.successful_render()
        with mock.patch.object(adapter, "find_powershell", return_value="powershell.exe"):
            with mock.patch.object(adapter.subprocess, "run", return_value=completed) as runner:
                exit_code = adapter.main(self.local_args())
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["adapter_status"], "rendered_local")
        self.assertTrue(payload["visual_evidence_ready"])
        self.assertFalse(payload["used_visual"])
        self.assertTrue(payload["source_unchanged"])
        command = runner.call_args.args[0]
        self.assertEqual(command[0], "powershell.exe")
        self.assertEqual(command[5], str(self.renderer.resolve()))

    def test_missing_renderer_is_advisory_unless_strict(self) -> None:
        with mock.patch.object(adapter, "find_local_renderer", return_value=None):
            advisory = adapter.main(
                ["--pptx", str(self.pptx), "--output", str(self.output)]
            )
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(advisory, 0)
        self.assertEqual(payload["adapter_status"], "unavailable")

        strict_output = self.root / "strict.json"
        with mock.patch.object(adapter, "find_local_renderer", return_value=None):
            strict = adapter.main(
                [
                    "--pptx",
                    str(self.pptx),
                    "--strict",
                    "--output",
                    str(strict_output),
                ]
            )
        self.assertEqual(strict, 2)

    def test_invalid_or_external_page_evidence_is_rejected(self) -> None:
        cases = ("invalid_png", "outside", "wrong_count")
        for case in cases:
            with self.subTest(case=case):
                output_dir = self.root / case
                output_dir.mkdir()
                pages_dir = output_dir if case != "outside" else self.root / f"{case}-external"
                pages_dir.mkdir(exist_ok=True)
                pages = [pages_dir / "page-1.png", pages_dir / "page-2.png"]
                for page in pages:
                    if case == "invalid_png":
                        page.write_bytes(b"not-png")
                    else:
                        write_minimal_png(page)
                response = {
                    "status": "success",
                    "page_count": 99 if case == "wrong_count" else 2,
                    "pages": [str(page) for page in pages],
                }
                completed = subprocess.CompletedProcess(
                    ["powershell"], 0, json.dumps(response), ""
                )
                sidecar = self.root / f"{case}.json"
                with mock.patch.object(
                    adapter, "find_powershell", return_value="powershell.exe"
                ):
                    with mock.patch.object(
                        adapter.subprocess, "run", return_value=completed
                    ):
                        adapter.main(
                            [
                                "--pptx",
                                str(self.pptx),
                                "--local-renderer",
                                str(self.renderer),
                                "--local-output-dir",
                                str(output_dir),
                                "--output",
                                str(sidecar),
                            ]
                        )
                payload = json.loads(sidecar.read_text(encoding="utf-8"))
                self.assertEqual(payload["adapter_status"], "failed")

    def test_output_paths_cannot_overwrite_source(self) -> None:
        before = self.pptx.read_bytes()
        exit_code = adapter.main(
            ["--pptx", str(self.pptx), "--output", str(self.pptx)]
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(self.pptx.read_bytes(), before)
        sidecar = self.pptx.parent / ".review" / "officecli-local.json"
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(payload["adapter_status"], "invalid_input")

        local_exit = adapter.main(
            [
                "--pptx",
                str(self.pptx),
                "--local-output-dir",
                str(self.pptx),
                "--output",
                str(self.output),
            ]
        )
        self.assertEqual(local_exit, 2)
        self.assertEqual(self.pptx.read_bytes(), before)

    def test_source_mutation_is_always_a_hard_failure(self) -> None:
        completed = self.successful_render()

        def mutating_runner(command, **kwargs):
            self.pptx.write_bytes(b"mutated")
            return completed

        with mock.patch.object(adapter, "find_powershell", return_value="powershell.exe"):
            with mock.patch.object(adapter.subprocess, "run", side_effect=mutating_runner):
                exit_code = adapter.main(self.local_args())
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["adapter_status"], "failed")
        self.assertFalse(payload["source_unchanged"])
        self.assertFalse(payload["visual_evidence_ready"])

    def test_render_result_slide_mismatch_is_a_warning(self) -> None:
        render_result = self.root / "render-result.json"
        render_result.write_text(json.dumps({"slide_count": 3}), encoding="utf-8")
        completed = self.successful_render()
        with mock.patch.object(adapter, "find_powershell", return_value="powershell.exe"):
            with mock.patch.object(adapter.subprocess, "run", return_value=completed):
                adapter.main(self.local_args() + ["--render-result", str(render_result)])
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertIn("does not match", " ".join(payload["warnings"]))

    def test_invalid_pptx_is_rejected(self) -> None:
        invalid = self.root / "invalid.pptx"
        invalid.write_text("not a zip", encoding="utf-8")
        exit_code = adapter.main(
            ["--pptx", str(invalid), "--output", str(self.output)]
        )
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["adapter_status"], "invalid_input")

    def test_default_sidecar_is_written(self) -> None:
        with mock.patch.object(adapter, "find_local_renderer", return_value=None):
            adapter.main(["--pptx", str(self.pptx)])
        self.assertTrue((self.pptx.parent / ".review" / "officecli-local.json").is_file())

    def test_nonpositive_timeout_is_rejected(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            adapter.main(["--pptx", str(self.pptx), "--timeout", "0"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
