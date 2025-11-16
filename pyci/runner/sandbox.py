import os
import subprocess
import sys
from pathlib import Path


ENV_ROOT = Path(".pyci_env")


def create_env(job_name: str):
    """
    Create a virtual environment for the given job.
    Returns the path to the Python executable inside the venv.
    """
    ENV_ROOT.mkdir(exist_ok=True)

    env_path = ENV_ROOT / job_name

    # Create venv only if not already created
    if not env_path.exists():
        print(f"🔧 Creating virtual environment for job '{job_name}'...")
        subprocess.run([sys.executable, "-m", "venv", str(env_path)], check=True)

    # Path to the Python executable inside the venv
    if os.name == "nt":
        python_exe = env_path / "Scripts" / "python.exe"
    else:
        python_exe = env_path / "bin" / "python"

    return python_exe
