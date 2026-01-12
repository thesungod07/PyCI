# PyCI

A Python-based Continuous Integration (CI) system that provides automated testing, building, and deployment capabilities for software projects.

## Overview

PyCI is a lightweight continuous integration framework designed to automate the software development workflow. It monitors repositories for changes, executes build and test pipelines, and provides feedback on code quality and test results.

## Features

- **Automated Build Pipeline**: Automatically builds projects when changes are detected
- **Test Execution**: Runs unit tests and integration tests as part of the CI pipeline
- **Flexible Configuration**: YAML-based configuration for defining build steps and test suites
- **Repository Monitoring**: Watches for changes in version control repositories
- **Build Status Reporting**: Provides clear feedback on build and test results
- **Extensible Architecture**: Plugin-based system for custom build steps and integrations

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Git (for repository monitoring)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/thesungod07/PyCI.git
cd PyCI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your project by creating a `.pyci.yml` file in your repository root (see Configuration section below).

## Usage

### Basic Usage

Run PyCI on your project:

```bash
python pyci.py --config .pyci.yml
```

### Command Line Options

- `--config`: Path to the configuration file (default: `.pyci.yml`)
- `--verbose`: Enable verbose logging
- `--dry-run`: Simulate the build without executing commands

## Configuration

Create a `.pyci.yml` file in your project root to define your CI pipeline:

```yaml
name: My Project CI

on:
  - push
  - pull_request

jobs:
  build:
    steps:
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/
      
      - name: Build project
        run: python setup.py build

  test:
    steps:
      - name: Run unit tests
        run: python -m unittest discover
      
      - name: Check code coverage
        run: coverage run -m pytest
```

### Configuration Options

- `name`: Project name
- `on`: Trigger events (push, pull_request, schedule)
- `jobs`: Define build and test jobs
- `steps`: Individual steps within each job
- `run`: Command to execute for each step

## Project Structure

```
PyCI/
├── pyci.py           # Main CI engine
├── config.py         # Configuration parser
├── runner.py         # Job and step executor
├── monitor.py        # Repository monitoring
├── utils.py          # Helper utilities
├── tests/            # Test suite
└── examples/         # Example configurations
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Run tests with coverage:

```bash
coverage run -m pytest
coverage report
```

## License

Apache License 2.0

## Support

For issues, questions, or contributions, please visit the [PyCI](https://github.com/thesungod07/PyCI).

## Roadmap

- [ ] Docker integration
- [ ] Parallel job execution
- [ ] Web dashboard for build results
- [ ] Integration with popular version control platforms
- [ ] Notification system (email, Slack, etc.)
- [ ] Artifact storage and management

## Acknowledgments

Built with Python and designed for developers who need a simple, extensible CI solution.

---

**Note**: This is an educational/personal project. For production use cases, consider established CI platforms like Jenkins, GitLab CI, or GitHub Actions.