import yaml

REQUIRED_TOP_LEVEL = ["jobs"]


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
