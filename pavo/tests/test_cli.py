from __future__ import annotations

import subprocess
import sys


def test_pavo_command():
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "pavo",
            "--help",
        ],
        capture_output=True,
    )
    assert output.returncode == 0
    assert "pavo" in output.stdout.decode()
