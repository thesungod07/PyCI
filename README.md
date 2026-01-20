# PyCI — A Lightweight, Extensible CI Runner in Python

**PyCI** is a lightweight, cross-platform Continuous Integration (CI) runner written entirely in Python.  
It executes YAML-defined workflows with **job isolation**, **dependency graphs**, **artifacts**, **matrix builds**, and **parallel execution**, inspired by systems like GitHub Actions and GitLab CI.

This project was built as a **systems-level utility project** and is suitable for use as:
- a learning CI engine,
- a local CI runner,
- a foundation for further CI/CD tooling,
- or a Google Summer of Code (GSoC) project.

---

## ✨ Features

### Core CI Capabilities
- 🧩 YAML-based workflow definitions
- ⚙️ Jobs & steps execution model
- 🔒 Per-job isolated Python virtual environments
- 📦 Dependency installation per job
- 🌍 Global & job-level environment variables
- 🧵 Parallel job execution
- ⏱️ Job-level timeouts
- 🧠 Dependency-aware scheduling (`needs:`)

### Artifacts
- 📤 Upload job artifacts
- 📥 Download artifacts from dependency jobs
- 📁 Organized artifact storage
- 🪟 Windows-safe paths (matrix jobs included)

### Advanced Features
- 🔁 Matrix jobs (Cartesian expansion)
- 📊 Detailed per-job logs
- ❌ Early failure detection & propagation
- 🖥️ Cross-platform support (Windows, Linux, macOS)

---

## 📦 Installation

### Prerequisites
- Python **3.9+**
- `pip`
- `venv` module (comes with Python)

### Install (editable mode recommended)

```bash
git clone https://github.com/<your-username>/pyci.git
cd pyci
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
