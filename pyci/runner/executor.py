import subprocess
import time
import os
from datetime import datetime
from pyci.utils.colors import Colors
from pyci.runner.sandbox import create_env


def run_jobs(config):
    jobs = config.get("jobs", {})

    # Ensure logs/ exists
    os.makedirs("logs", exist_ok=True)

    for job_name, job_data in jobs.items():

        print(Colors.bold(f"\n=== Running job: {job_name} ==="))

        python_exe = create_env(job_name)

        steps = job_data.get("steps", [])
        if not isinstance(steps, list):
            print(Colors.red(f"❌ Invalid steps in job '{job_name}' — must be a list"))
            continue

        # Create log file path
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_path = f"logs/{job_name}_{timestamp}.log"

        with open(log_path, "w", encoding="utf-8") as logfile:

            logfile.write(f"=== Logs for job: {job_name} ===\n")
            logfile.write(f"Started: {timestamp}\n\n")

            for step in steps:
                print(Colors.blue(f"→ {step}"))

                logfile.write(f"\n→ {step}\n")

                start = time.time()

                if step.startswith("python "):  
                    step = step.replace("python ", f'"{python_exe}" ', 1)

                install_cmds = job_data.get("install", [])

                if install_cmds:
                    print(Colors.yellow(f"\n📦 Installing dependencies for job '{job_name}'..."))
                    logfile.write("\n=== Installing dependencies ===\n")

                    for cmd in install_cmds:
                        logfile.write(f"\n→ {cmd}\n")
                        print(Colors.blue(f"→ {cmd}"))

                        # Replace python with venv python
                        if cmd.startswith("python"):
                            cmd = cmd.replace("python", str(python_exe), 1)

                        result = subprocess.run(
                            cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )

                        logfile.write(result.stdout)
                        logfile.write(result.stderr)

                        if result.returncode != 0:
                            print(Colors.red("❌ Dependency installation failed."))
                            logfile.write("❌ Dependency installation failed.\n")
                            return   # stop job entirely

                    print(Colors.green("✔ Dependencies installed successfully\n"))


                result = subprocess.run(
                    step,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                duration = time.time() - start

                # Write outputs to log
                logfile.write(result.stdout + "\n")
                logfile.write(result.stderr + "\n")

                if result.returncode == 0:
                    print(Colors.green(f"✔ Success ({duration:.2f}s)\n"))
                    logfile.write(f"✔ Success ({duration:.2f}s)\n")
                else:
                    print(Colors.red(f"❌ Failed ({duration:.2f}s)"))
                    print(Colors.red("Stopping job early due to failure."))

                    logfile.write(f"❌ Failed ({duration:.2f}s)\n")
                    logfile.write("Stopping job early due to failure.\n")

                    break

        print(Colors.yellow(f"📄 Log saved at: {log_path}"))
