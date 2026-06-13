"""Cross-platform task runner. Usage: ``invoke <task>`` (alias ``inv``).

Run ``inv --list`` to see all tasks.
"""

from __future__ import annotations

import shutil

from invoke import task


@task
def install(c, dev=True):
    """Install runtime (or dev) deps into the active venv, plus this package in editable mode."""
    req = "requirements-dev.txt" if dev else "requirements.txt"
    c.run("python -m pip install --upgrade pip")
    c.run(f"python -m pip install -r {req}")
    c.run("python -m pip install -e .")


@task
def lint(c):
    """Run ruff lint."""
    c.run("ruff check src tests")


@task
def fmt(c):
    """Auto-format with ruff."""
    c.run("ruff format src tests")
    c.run("ruff check --fix src tests")


@task
def typecheck(c):
    """Run mypy on the package."""
    c.run("mypy src")


@task(help={"slow": "Include @slow tests (loads the model).", "cov": "Emit coverage report."})
def test(c, slow=False, cov=False):
    """Run pytest. By default, excludes @slow tests."""
    args = ["pytest"]
    if not slow:
        args += ["-m", "\"not slow\""]
    if cov:
        args += ["--cov=src/cpl_crop", "--cov-report=term-missing"]
    c.run(" ".join(args))


@task
def smoke(c):
    """Phase 1 smoke test: load model + predict on a synthetic image."""
    c.run("pytest -m slow -v tests/test_model_loader.py")


@task(help={"reload": "Auto-reload on code changes (dev only)."})
def serve(c, reload=False):
    """Start the FastAPI server via uvicorn in factory mode."""
    cmd = (
        "python -m uvicorn cpl_crop.api.app:create_app "
        "--factory --host 127.0.0.1 --port 8000"
    )
    if reload:
        cmd += " --reload"
    c.run(cmd)


@task(help={"port": "Streamlit server port (default 8501)."})
def ui(c, port=8501):
    """Start the Streamlit demo UI (assumes `inv serve` is running)."""
    c.run(f"python -m streamlit run streamlit_app/streamlit_app.py --server.port {port}")


@task
def check(c):
    """Run lint + typecheck + fast tests in one shot."""
    lint(c)
    typecheck(c)
    test(c)


@task
def clean(c):
    """Remove build artifacts and caches."""
    for d in (
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        "src/cpl_crop.egg-info",
        "cpl_crop_disease.egg-info",
    ):
        shutil.rmtree(d, ignore_errors=True)
