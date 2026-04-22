import sys
from pathlib import Path
import types
from unittest import mock
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Avoid importing the real textual viewer in unit tests.
fake_viewer_module = types.ModuleType("viewer")
fake_viewer_module.CodeViewer = mock.Mock
sys.modules["viewer"] = fake_viewer_module

import main as main_module


class MainTests(unittest.TestCase):
    def test_main_uses_command_source(self) -> None:
        fake_app = mock.Mock()
        with mock.patch.object(main_module, "CodeViewer", return_value=fake_app):
            with mock.patch.object(sys, "argv", ["codoscope", "-c", "x = 1"]):
                main_module.main(["codoscope", "-c", "x = 1"])

        self.assertEqual(fake_app.startup_code, "x = 1")
        fake_app.run.assert_called_once()

    def test_main_rejects_ambiguous_inputs(self) -> None:
        with self.assertRaises(SystemExit):
            with mock.patch.object(sys, "argv", ["codoscope", "-c", "x = 1", "-m", "json"]):
                main_module.main(["codoscope", "-c", "x = 1", "-m", "json"])

    def test_main_loads_file_contents(self) -> None:
        fake_app = mock.Mock()
        with mock.patch.object(main_module, "CodeViewer", return_value=fake_app):
            with mock.patch.object(main_module.Path, "read_text", return_value="print('ok')") as read_text:
                with mock.patch.object(sys, "argv", ["codoscope", "sample.py"]):
                    main_module.main(["codoscope", "sample.py"])

        read_text.assert_called_once()
        self.assertEqual(fake_app.startup_code, "print('ok')")
        fake_app.run.assert_called_once()

    def test_main_loads_module_source(self) -> None:
        fake_app = mock.Mock()
        fake_module = mock.Mock(__file__="/tmp/fake_module.py")
        with mock.patch.object(main_module, "CodeViewer", return_value=fake_app):
            with mock.patch.object(main_module.importlib, "import_module", return_value=fake_module):
                with mock.patch.object(main_module.Path, "read_text", return_value="value = 42"):
                    with mock.patch.object(sys, "argv", ["codoscope", "-m", "fake.module"]):
                        main_module.main(["codoscope", "-m", "fake.module"])

        self.assertEqual(fake_app.startup_code, "value = 42")
        fake_app.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
