import subprocess
import time
import os
import shutil
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from pyci.utils.colors import Colors
from pyci.runner.sandbox import create_env


# ---------------- UTILS ---------------- #

def safe_job_id(job_name: str) -> str:
    """Filesystem-safe job identifier (important for Windows)."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", job_name)


def check_timeout(job_name, job_timeout, job_start_time, logfile):
    if job_timeout is None:
        return False

    elapsed = time.time() - job_start_time
    if elapsed > job_timeout:
        msg = f"❌ Job '{job_name}' timed out after {job_timeout} seconds\n"
        print(Colors.red(msg.strip()))
        logfile.write(msg)
        return True

    return False


# ---------------- JOB EXECUTION ---------------- #

def run_single_job(job_name, job_data):
    job_id = safe_job_id(job_name)
    job_timeout = job_data.get("timeout")
    job_start_time = time.time()

    os.makedirs("logs", exist_ok=True)

    # Create sandbox using SAFE job id
    python_exe = create_env(job_id)

    # Merge env correctly
    env = {**os.environ}
    env.update({str(k): str(v) for k, v in job_data.get("env", {}).items()})

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = f"logs/{job_id}_{timestamp}.log"

    with open(log_path, "w", encoding="utf-8") as logfile:
        logfile.write(f"=== Logs for job: {job_name} ===\n")
        logfile.write(f"Started: {timestamp}\n\n")

        print(Colors.bold(f"\n=== Running job: {job_name} ==="))

        # -------- FETCH ARTIFACTS -------- #
        uses = job_data.get("uses_artifacts", [])
        if isinstance(uses, str):
            uses = [uses]

        if uses:
            print(Colors.yellow(f"\n📦 Fetching artifacts for job '{job_name}'..."))
            logfile.write("\n=== Fetching Artifacts ===\n")

            for dep in uses:
                dep_id = safe_job_id(dep)
                src_dir = f"artifacts/{dep_id}"
                dest_dir = f"artifacts_used/{job_id}/{dep_id}"

                if not os.path.exists(src_dir):
                    logfile.write(f"❌ Missing artifacts from: {dep}\n")
                    print(Colors.red(f"❌ Artifacts from job '{dep}' not found"))
                    return (job_name, False, log_path)

                os.makedirs(dest_dir, exist_ok=True)

                for file in os.listdir(src_dir):
                    shutil.copy(
                        os.path.join(src_dir, file),
                        os.path.join(dest_dir, file)
                    )
                    logfile.write(f"✔ Pulled: {dep}/{file}\n")
                    print(Colors.green(f"✔ Pulled artifact: {dep}/{file}"))

        if check_timeout(job_name, job_timeout, job_start_time, logfile):
            return (job_name, False, log_path)

        # -------- INSTALL -------- #
        install_cmds = job_data.get("install", [])
        if install_cmds:
            print(Colors.yellow(f"\n📦 Installing dependencies for job '{job_name}'..."))
            logfile.write("\n=== Installing Dependencies ===\n")

            for cmd in install_cmds:
                logfile.write(f"\n→ {cmd}\n")
                print(Colors.blue(f"→ {cmd}"))

                if cmd.startswith("python"):
                    cmd = cmd.replace("python", str(python_exe), 1)

                result = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )

                logfile.write(result.stdout)
                logfile.write(result.stderr)

                if result.returncode != 0:
                    print(Colors.red("❌ Dependency installation failed"))
                    logfile.write("❌ Dependency installation failed\n")
                    return (job_name, False, log_path)

            print(Colors.green("✔ Dependencies installed successfully\n"))

        if check_timeout(job_name, job_timeout, job_start_time, logfile):
            return (job_name, False, log_path)

        # -------- STEPS -------- #
        for step in job_data.get("steps", []):
            if check_timeout(job_name, job_timeout, job_start_time, logfile):
                return (job_name, False, log_path)

            print(Colors.blue(f"→ {step}"))
            logfile.write(f"\n→ {step}\n")

            start = time.time()

            if step.startswith("python"):
                step = step.replace("python", str(python_exe), 1)

            result = subprocess.run(
                step,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            duration = time.time() - start
            logfile.write(result.stdout)
            logfile.write(result.stderr)

            if result.returncode == 0:
                print(Colors.green(f"✔ Success ({duration:.2f}s)\n"))
                logfile.write(f"✔ Success ({duration:.2f}s)\n")
            else:
                print(Colors.red(f"❌ Failed ({duration:.2f}s)"))
                print(Colors.red("Stopping job early due to failure."))
                logfile.write(f"❌ Failed ({duration:.2f}s)\n")
                logfile.write("Stopping job early due to failure.\n")
                return (job_name, False, log_path)

        # -------- SAVE ARTIFACTS -------- #
        artifacts = job_data.get("artifacts", [])
        if artifacts:
            artifacts_dir = f"artifacts/{job_id}"
            os.makedirs(artifacts_dir, exist_ok=True)

            logfile.write("\n=== Saving Artifacts ===\n")
            print(Colors.yellow(f"\n📦 Saving artifacts for job '{job_name}'..."))

            for path in artifacts:
                if os.path.exists(path):
                    shutil.copy(path, artifacts_dir)
                    logfile.write(f"✔ Saved: {path}\n")
                    print(Colors.green(f"✔ Saved artifact: {path}"))
                else:
                    logfile.write(f"❌ Not found: {path}\n")
                    print(Colors.red(f"❌ Artifact not found: {path}"))

            print(Colors.yellow(f"Artifacts stored in: {artifacts_dir}\n"))

        print(Colors.yellow(f"📄 Log saved at: {log_path}"))
        return (job_name, True, log_path)


# ---------------- WORKFLOW EXECUTION ---------------- #

def order_jobs_by_dependencies(jobs):
    graph = {}
    indegree = {}

    for job_name, job_data in jobs.items():
        needs = job_data.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]

        graph[job_name] = needs
        indegree[job_name] = len(needs)

    ordered = []
    ready = [j for j, d in indegree.items() if d == 0]

    while ready:
        job = ready.pop(0)
        ordered.append(job)
        for j, deps in graph.items():
            if job in deps:
                indegree[j] -= 1
                if indegree[j] == 0:
                    ready.append(j)

    if len(ordered) != len(jobs):
        raise SystemExit("❌ Cyclic dependency detected in 'needs:'")

    return ordered


def run_jobs(config, parallel=False):
    jobs = config.get("jobs", {})
    order = order_jobs_by_dependencies(jobs)

    if not parallel:
        for job_name in order:
            run_single_job(job_name, jobs[job_name])
        return

    print(Colors.bold("\n🚀 Running jobs in parallel with dependency resolution...\n"))
    completed = {}

    with ThreadPoolExecutor() as executor:
        futures = {}

        for job_name in order:
            needs = jobs[job_name].get("needs", [])
            if isinstance(needs, str):
                needs = [needs]

            if any(completed.get(dep) is False for dep in needs):
                print(Colors.red(f"❌ Skipping '{job_name}' due to failed dependency"))
                completed[job_name] = False
                continue

            futures[job_name] = executor.submit(
                run_single_job, job_name, jobs[job_name]
            )

        for job_name, future in futures.items():
            _, success, _ = future.result()
            completed[job_name] = success
