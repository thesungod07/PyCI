import subprocess
import time
import os
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

    print(Colors.yellow(f"📄 Log saved at: {log_path}"))
    return (job_name, True, log_path)


# Run all jobs (sequentially or in parallel)
def run_jobs(config, parallel=False):
    jobs = config.get("jobs", {})

    if not parallel:
        # Sequential mode (previous behavior)
        for job_name, job_data in jobs.items():
            run_single_job(job_name, job_data)
        return

    # PARALLEL MODE
    print(Colors.bold("\n🚀 Running jobs in parallel...\n"))

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(run_single_job, name, data): name
            for name, data in jobs.items()
        }

        for future in as_completed(futures):
            job_name = futures[future]
            try:
                name, success, log_path = future.result()
                if success:
                    print(Colors.green(f"✔ Job '{name}' completed successfully"))
                else:
                    print(Colors.red(f"❌ Job '{name}' failed"))
            except Exception as e:
                print(Colors.red(f"❌ Job '{job_name}' crashed with error: {e}"))
