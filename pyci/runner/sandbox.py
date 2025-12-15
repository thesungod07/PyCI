import os
import sys
import subprocess
from pathlib import Path


def create_env(job_id: str) -> Path:
    """
    Create (or reuse) a virtual environment for a job.
    IMPORTANT: job_id MUST be filesystem-safe.
    """
    base_dir = Path(".pyci_env")
    env_dir = base_dir / job_id

    if not env_dir.exists():
        print(f"🔧 Creating virtual environment for job '{job_id}'...")
        subprocess.check_call(
            [sys.executable, "-m", "venv", str(env_dir)]
        )

    # Return python executable path
    if os.name == "nt":  # Windows
        python_exe = env_dir / "Scripts" / "python.exe"
    else:
        python_exe = env_dir / "bin" / "python"

    return python_exe
