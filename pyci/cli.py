import argparse
from pyci.runner.loader import load_config
from pyci.runner.executor import run_jobs


def main():
    parser = argparse.ArgumentParser(prog="pyci", description="PyCI Runner")

    sub = parser.add_subparsers(dest="command")

    # pyci run
    run_cmd = sub.add_parser("run", help="Run CI jobs defined in .pyci.yml")
    run_cmd.add_argument("--file", default=".pyci.yml", help="Path to config file")

    # pyci validate
    val_cmd = sub.add_parser("validate", help="Validate CI configuration")
    val_cmd.add_argument("--file", default=".pyci.yml")

    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.file)
        run_jobs(config)

    elif args.command == "validate":
        load_config(args.file)
        print("Configuration OK ✔")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
