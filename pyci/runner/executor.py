import subprocess
import time
import os
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from pyci.utils.colors import Colors
from pyci.runner.sandbox import create_env


# Run a single job
def run_single_job(job_name, job_data):
    # Prepare logs folder
    os.makedirs("logs", exist_ok=True)

    # Prepare virtual environment
    python_exe = create_env(job_name)

    global_env = job_data.get("env", {})
    job_env = job_data.get("env", {})

    env = {**global_env, **job_env}
    env = {str(k): str(v) for k, v in env.items()}

    # Create log file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = f"logs/{job_name}_{timestamp}.log"

    with open(log_path, "w", encoding="utf-8") as logfile:
        logfile.write(f"=== Logs for job: {job_name} ===\n")
        logfile.write(f"Started: {timestamp}\n\n")

        print(Colors.bold(f"\n=== Running job: {job_name} ==="))

        uses = job_data.get("uses_artifacts", [])

        if uses:
            print(Colors.yellow(f"\n📦 Fetching artifacts for job '{job_name}'..."))
            logfile.write("\n=== Fetching Artifacts ===\n")

            for dep in uses:
                src_dir = f"artifacts/{dep}"
                dest_dir = f"artifacts_used/{job_name}/{dep}"

                if not os.path.exists(src_dir):
                    logfile.write(f"❌ Missing artifacts from: {dep}\n")
                    print(Colors.red(f"❌ Artifacts from job '{dep}' not found"))
                    return (job_name, False, log_path)

                os.makedirs(dest_dir, exist_ok=True)

                for file in os.listdir(src_dir):
                    src = os.path.join(src_dir, file)
                    dst = os.path.join(dest_dir, file)

                    shutil.copy(src, dst)
                    logfile.write(f"✔ Pulled: {dep}/{file}\n")
                    print(Colors.green(f"✔ Pulled artifact: {dep}/{file}"))
        
        install_cmds = job_data.get("install", [])

        if install_cmds:
            print(Colors.yellow(f"\n📦 Installing dependencies for job '{job_name}'..."))
            logfile.write("=== Installing dependencies ===\n")

            for cmd in install_cmds:
                logfile.write(f"\n→ {cmd}\n")
                print(Colors.blue(f"→ {cmd}"))

                # Replace python with sandbox python
                if cmd.startswith("python"):
                    cmd = cmd.replace("python", str(python_exe), 1)

                result = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, **env}
                )


                logfile.write(result.stdout)
                logfile.write(result.stderr)

                if result.returncode != 0:
                    print(Colors.red("❌ Dependency installation failed."))
                    logfile.write("❌ Dependency installation failed.\n")
                    return (job_name, False, log_path)

            print(Colors.green("✔ Dependencies installed successfully\n"))

        steps = job_data.get("steps", [])

        for step in steps:
            print(Colors.blue(f"→ {step}"))
            logfile.write(f"\n→ {step}\n")

            start = time.time()

            # Replace python with sandbox python
            if step.startswith("python"):
                step = step.replace("python", str(python_exe), 1)

            result = subprocess.run(
                step,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
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

        artifacts = job_data.get("artifacts", [])
        if artifacts:
            artifacts_dir = f"artifacts/{job_name}"
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



# Run all jobs (sequentially or in parallel)
def run_jobs(config, parallel=False):
    jobs = config.get("jobs", {})

    if not parallel:
        order = order_jobs_by_dependencies(jobs)

        for job_name, job_data in jobs.items():
            run_single_job(job_name, jobs[job_name])
        return

        # PARALLEL MODE WITH DEPENDENCY TRACKING
        print(Colors.bold("\n🚀 Running jobs in parallel with dependency resolution...\n"))

        order = order_jobs_by_dependencies(jobs)

        completed = {}
        futures = {}

        with ThreadPoolExecutor() as executor:
            for job_name in order:
                needs = jobs[job_name].get("needs", [])

                # Wait for dependencies
                for dep in needs if isinstance(needs, list) else [needs]:
                    # If dependency failed, skip this job
                    if completed.get(dep) is False:
                        print(Colors.red(f"❌ Skipping '{job_name}' because dependency '{dep}' failed"))
                        completed[job_name] = False
                        break
                else:
                    # Run job
                    futures[job_name] = executor.submit(
                        run_single_job, job_name, jobs[job_name]
                    )

                # Check finished jobs
                for name, future in list(futures.items()):
                    if future.done():
                        _, success, _ = future.result()
                        completed[name] = success
                        del futures[name]

        # Wait for remaining
        for name, future in futures.items():
            _, success, _ = future.result()
            completed[name] = success

def order_jobs_by_dependencies(jobs):
    # Build graph
    graph = {}
    indegree = {}

    for job_name, job_data in jobs.items():
        needs = job_data.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]

        graph[job_name] = needs
        indegree[job_name] = len(needs)

    # Kahn’s Topological Sort
    ordered = []
    ready = [job for job, d in indegree.items() if d == 0]

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
