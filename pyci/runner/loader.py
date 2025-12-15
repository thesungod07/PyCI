import yaml
import itertools
import copy

REQUIRED_TOP_LEVEL = ["jobs"]

def expand_matrix_jobs(jobs):
    expanded = {}

    for job_name, job_data in jobs.items():
        matrix = job_data.get("matrix")

        # No matrix → keep job as-is
        if not matrix:
            expanded[job_name] = job_data
            continue

        if not isinstance(matrix, dict):
            raise SystemExit(f"❌ 'matrix' in job '{job_name}' must be a dictionary")

        keys = list(matrix.keys())
        values = list(matrix.values())

        for k, v in matrix.items():
            if not isinstance(v, list):
                raise SystemExit(
                    f"❌ Matrix values for '{k}' in job '{job_name}' must be a list"
                )

        # Cartesian product
        for combo in itertools.product(*values):
            suffix = ",".join(f"{k}={v}" for k, v in zip(keys, combo))
            new_job_name = f"{job_name}[{suffix}]"

            new_job = copy.deepcopy(job_data)
            new_job.pop("matrix")

            # Inject matrix vars as env
            env = new_job.get("env", {})
            env.update({k: str(v) for k, v in zip(keys, combo)})
            new_job["env"] = env

            expanded[new_job_name] = new_job

    return expanded


def load_config(path: str):    
    # Loading YAML file safely
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise SystemExit(f"❌ Configuration file not found: {path}")
    except yaml.YAMLError as e:
        raise SystemExit(f"❌ YAML syntax error in {path}:\n{e}")

    # Empty file check
    if data is None:
        raise SystemExit(f"❌ {path} is empty or invalid YAML.")

    # Validate top-level structure
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            raise SystemExit(f"❌ Missing required top-level key: '{key}'")

    jobs = data["jobs"]
    jobs = expand_matrix_jobs(jobs)
    data["jobs"] = jobs
    
    if not isinstance(jobs, dict):
        raise SystemExit("❌ 'jobs' must be a dictionary of job_name → job_config")

    if len(jobs) == 0:
        raise SystemExit("❌ No jobs defined under 'jobs:'")

    # Validate each job
    for job_name, job_data in jobs.items():
        if not isinstance(job_data, dict):
            raise SystemExit(f"❌ Job '{job_name}' must be a mapping, not {type(job_data).__name__}")

        if "steps" not in job_data:
            raise SystemExit(f"❌ Job '{job_name}' is missing required key: 'steps'")
        
        # Validate global env
        if "env" in data:
            if not isinstance(data["env"], dict):
                raise SystemExit("❌ Top-level 'env' must be a dictionary")
        
        # Validate 'needs' (optional)
        if "needs" in job_data:
            needs = job_data["needs"]

            if isinstance(needs, str):
                needs = [needs]

            if not isinstance(needs, list):
                raise SystemExit(f"❌ 'needs' in job '{job_name}' must be a string or list of strings")

            for dep in needs:
                if dep not in data["jobs"]:
                    raise SystemExit(
                        f"❌ Job '{job_name}' references unknown dependency '{dep}' in 'needs'"
                    )

        # Validate install section (optional)
        if "install" in job_data:
            install_cmds = job_data["install"]

            if not isinstance(install_cmds, list):
                raise SystemExit(f"❌ 'install' in job '{job_name}' must be a list")

            for cmd in install_cmds:
                if not isinstance(cmd, str):
                    raise SystemExit(
                        f"❌ Invalid install command in job '{job_name}'. "
                        f"All install commands must be strings.\n"
                        f"   Offending value: {cmd}"
                    )
        
        if "artifacts" in job_data:
            artifacts = job_data["artifacts"]

            if not isinstance(artifacts, list):
                raise SystemExit(f"❌ 'artifacts' in job '{job_name}' must be a list")

            for path in artifacts:
                if not isinstance(path, str):
                    raise SystemExit(
                        f"❌ Invalid artifact path in job '{job_name}'. Must be a string.\n"
                        f"   Offending value: {path}"
                    )

        # Validate artifact usage (optional)
        if "uses_artifacts" in job_data:
            uses = job_data["uses_artifacts"]

            # Convert string → list
            if isinstance(uses, str):
                uses = [uses]
                job_data["uses_artifacts"] = uses

            if not isinstance(uses, list):
                raise SystemExit(f"❌ 'uses_artifacts' in job '{job_name}' must be a string or list")

            for dep in uses:
                if dep not in data["jobs"]:
                    raise SystemExit(
                        f"❌ Job '{job_name}' requests artifacts from unknown job '{dep}'"
                    )

        # Validate timeout (optional)
        if "timeout" in job_data:
            timeout = job_data["timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise SystemExit(
                    f"❌ 'timeout' in job '{job_name}' must be a positive number (seconds)"
                )


        # Validate environment variables (optional)
        if "env" in job_data:
            if not isinstance(job_data["env"], dict):
                raise SystemExit(f"❌ 'env' in job '{job_name}' must be a dictionary")


        steps = job_data["steps"]

        if not isinstance(steps, list):
            raise SystemExit(f"❌ 'steps' in job '{job_name}' must be a list")

        if len(steps) == 0:
            raise SystemExit(f"❌ Job '{job_name}' has no steps defined")

        # Check each step is a string command
        for s in steps:
            if not isinstance(s, str):
                raise SystemExit(
                    f"❌ Invalid step in job '{job_name}': all steps must be strings.\n"
                    f"   Offending value: {s}"
                )

    return data
