import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('runtime', Path(__file__).resolve().parents[1] / 'scripts/hermes_runtime.py')
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeGuardTests(unittest.TestCase):
    def test_windows_install_is_rejected_before_any_subprocess(self):
        with patch.object(runtime.platform, 'system', return_value='Windows'), \
             patch.object(runtime.sys, 'argv', ['runtime', 'install']), \
             patch.object(runtime.subprocess, 'run') as run, \
             patch.object(runtime.subprocess, 'check_output') as read, \
             contextlib.redirect_stderr(io.StringIO()), \
             self.assertRaises(SystemExit) as error:
            runtime.main()
        self.assertEqual(error.exception.code, 2)
        run.assert_not_called()
        read.assert_not_called()


if __name__ == '__main__':
    unittest.main()
