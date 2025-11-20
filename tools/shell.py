# tools/shell.py
import subprocess
import shlex
import os
from pathlib import Path

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", ".")).resolve()

def run_command(command: str, timeout: int = 120) -> dict:
    """
    Run a shell command in PROJECT_ROOT.
    Returns stdout, stderr, and exit code.
    """
    try:
        result = subprocess.run(
            shlex.split(command),
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
        )
        return {
            "ok": True,
            "exit_code": result.returncode,
            "stdout": result.stdout[-8000:],  # clip for token limits
            "stderr": result.stderr[-8000:],
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error": "timeout",
            "stdout": (e.stdout or "")[-4000:],
            "stderr": (e.stderr or "")[-4000:],
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }
