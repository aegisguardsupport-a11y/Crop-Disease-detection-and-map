"""Drive the Kaggle CLI from kiro-cli.

Reads the Kaggle username from the canonical ``~/.kaggle/kaggle.json``
file, fills in the kernel id, pushes the notebook, and polls until it
finishes.

The Kaggle API key is *never* read or echoed by this script — only the
``username`` field. The actual authentication happens inside the
``kaggle`` CLI which reads the same file.

Usage::

    python scripts/kaggle_run.py verify                  # auth check
    python scripts/kaggle_run.py push   01_dataset_assembly
    python scripts/kaggle_run.py status 01_dataset_assembly
    python scripts/kaggle_run.py output 01_dataset_assembly
    python scripts/kaggle_run.py run    01_dataset_assembly   # all-in-one
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KAGGLE_DIR = ROOT / "kaggle"
OUTPUTS_DIR = ROOT / "outputs"
USERNAME_PLACEHOLDER = "__USERNAME__"
POLL_INTERVAL_S = 30
# Kaggle's CLI prints lines like:  ... has status "KernelWorkerStatus.RUNNING"
# We strip the prefix and lowercase before comparing.
TERMINAL_STATUSES = {"complete", "error", "failed", "cancelled", "cancelacknowledged"}


def _normalise_status(s: str) -> str:
    """KernelWorkerStatus.RUNNING -> running, etc."""
    s = s.strip().rsplit(".", 1)[-1]
    return s.lower()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_kaggle_username() -> str:
    """Return the username field from ~/.kaggle/kaggle.json. Never returns the key."""
    creds_path = Path.home() / ".kaggle" / "kaggle.json"
    if not creds_path.exists():
        sys.exit(
            f"ERROR: Kaggle credentials not found at {creds_path}\n"
            "Place your kaggle.json there. See README.md."
        )
    try:
        creds = json.loads(creds_path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {creds_path} is not valid JSON: {e}")
    user = creds.get("username")
    if not user or not isinstance(user, str):
        sys.exit(
            f"ERROR: 'username' field missing in {creds_path}\n"
            "Re-download kaggle.json from your Kaggle Account API page."
        )
    return user


def stage_path(stage: str) -> Path:
    p = KAGGLE_DIR / stage
    if not p.is_dir():
        available = sorted(d.name for d in KAGGLE_DIR.iterdir() if d.is_dir())
        sys.exit(f"ERROR: stage '{stage}' not found. Available: {available}")
    return p


def metadata_path(stage: str) -> Path:
    p = stage_path(stage) / "kernel-metadata.json"
    if not p.exists():
        sys.exit(f"ERROR: kernel-metadata.json missing in {p.parent}")
    return p


def load_metadata(stage: str) -> dict:
    return json.loads(metadata_path(stage).read_text())


def save_metadata(stage: str, data: dict) -> None:
    metadata_path(stage).write_text(json.dumps(data, indent=2) + "\n")


def fill_username(data: dict, username: str) -> dict:
    """Replace __USERNAME__ in id and kernel_sources with the actual username."""
    if isinstance(data.get("id"), str):
        data["id"] = data["id"].replace(USERNAME_PLACEHOLDER, username)
    if isinstance(data.get("kernel_sources"), list):
        data["kernel_sources"] = [
            s.replace(USERNAME_PLACEHOLDER, username) for s in data["kernel_sources"]
        ]
    return data


def kernel_id(stage: str) -> str:
    data = fill_username(load_metadata(stage), get_kaggle_username())
    if "/" not in data.get("id", ""):
        sys.exit(
            f"ERROR: kernel id in {stage}/kernel-metadata.json is malformed: {data.get('id')!r}"
        )
    return data["id"]


def kaggle_command() -> list[str]:
    """Locate the kaggle CLI: prefer PATH, fall back to the venv that runs this script."""
    if shutil.which("kaggle"):
        return ["kaggle"]
    # Fall back to a kaggle binary next to the Python interpreter (venv layout)
    py_dir = Path(sys.executable).parent
    for name in ("kaggle.exe", "kaggle"):
        candidate = py_dir / name
        if candidate.exists():
            return [str(candidate)]
    # Final fallback: invoke as a module
    return [sys.executable, "-m", "kaggle"]


def run_kaggle(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """Run the kaggle CLI with the given arguments. Forces UTF-8 stdout.

    Always captures bytes and decodes with errors='replace' so a stray
    Unicode glyph the kaggle CLI tries to print on a CP1252 Windows
    console doesn't crash the whole command.
    """
    cmd = [*kaggle_command(), *args]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(cmd, capture_output=True, env=env)
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    if not capture:
        # Print captured streams so the user can see progress / errors,
        # but only after the subprocess has finished — avoids the live
        # codec-error path entirely.
        if stdout:
            print(stdout, end="")
        if stderr:
            sys.stderr.write(stderr)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, stdout, stderr)
    return subprocess.CompletedProcess(cmd, 0, stdout, stderr)


def ensure_kaggle_installed() -> None:
    cmd = kaggle_command()
    # If we're falling back to `python -m kaggle`, just attempt a trivial call
    try:
        subprocess.run([*cmd, "--version"], check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit(
            "ERROR: 'kaggle' CLI not found.\n"
            "Run: pip install -r requirements.txt   (in your active Python env)"
        )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_verify() -> None:
    ensure_kaggle_installed()
    user = get_kaggle_username()
    print(f"Kaggle username: {user}")
    print("Listing your most recent kernels (auth check)...")
    run_kaggle("kernels", "list", "--mine", "-p", "1")
    print("\nAuth OK.")


def _materialise_metadata(stage: str) -> str:
    """Fill placeholders in kernel-metadata.json and write it back; return kernel id."""
    user = get_kaggle_username()
    data = load_metadata(stage)
    data = fill_username(data, user)
    save_metadata(stage, data)
    return data["id"]


def cmd_push(stage: str) -> None:
    ensure_kaggle_installed()
    p = stage_path(stage)
    kid = _materialise_metadata(stage)

    # If a notebook.py exists, regenerate notebook.ipynb from it (single source of truth).
    py_path = p / "notebook.py"
    if py_path.exists():
        from py_to_ipynb import py_to_ipynb  # local import; same scripts/ dir

        ipynb_path = py_path.with_suffix(".ipynb")
        print(f"Regenerating {ipynb_path.name} from {py_path.name} ...")
        py_to_ipynb(py_path, ipynb_path)

    print(f"Pushing kernel {kid} from {p} ...")
    run_kaggle("kernels", "push", "-p", str(p))
    print(f"Pushed: https://www.kaggle.com/code/{kid}")


def cmd_status(stage: str, follow: bool = False) -> str:
    ensure_kaggle_installed()
    kid = kernel_id(stage)
    while True:
        result = run_kaggle("kernels", "status", kid, capture=True)
        line = result.stdout.strip()
        print(line)
        # Extract the quoted status word, e.g. "KernelWorkerStatus.RUNNING"
        status_word = ""
        if '"' in line:
            try:
                status_word = _normalise_status(line.split('"')[1])
            except IndexError:
                pass
        if not follow or status_word in TERMINAL_STATUSES:
            return status_word
        time.sleep(POLL_INTERVAL_S)


def cmd_output(stage: str, keep: list[str] | None = None) -> None:
    """Download outputs of a finished kernel.

    If ``keep`` is provided, after the download we keep only files whose
    *relative* path matches at least one of the provided fnmatch patterns
    (e.g. ``"*.csv"``, ``"*.json"``, ``"summary*"``). Everything else is
    deleted to keep the local copy small.

    Uses the Kaggle Python API (not the CLI) so we don't trip over
    Windows console encoding issues with non-ASCII filenames.
    """
    import fnmatch

    ensure_kaggle_installed()
    kid = kernel_id(stage)
    out_dir = OUTPUTS_DIR / stage
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading output of {kid} into {out_dir} ...")
    print("(this can take a while; per-file logs are suppressed)")

    # Force the Python interpreter (and the kaggle library) to use UTF-8.
    os.environ["PYTHONIOENCODING"] = "utf-8"

    from kaggle import api as kapi  # type: ignore[import-untyped]

    kapi.authenticate()
    # Signature: kernels_output(kernel, path, file_pattern=None, force=False, quiet=True)
    # file_pattern is a REGEX applied server-side. If --keep was provided, build
    # a pattern from the suffixes so we don't pull all 9000+ images.
    file_pattern: str | None = None
    if keep:
        # Convert simple "*.csv", "*.json" globs to a regex like ".*\.(csv|json|png)$"
        suffixes: list[str] = []
        for pat in keep:
            if pat.startswith("*.") and "/" not in pat:
                suffixes.append(pat[2:])
        if suffixes and len(suffixes) == len(keep):
            file_pattern = r".*\.(" + "|".join(suffixes) + r")$"
            print(f"Server-side filter: {file_pattern}")
    kapi.kernels_output(
        kernel=kid,
        path=str(out_dir),
        file_pattern=file_pattern,
        force=True,
        quiet=True,
    )
    print("Download complete.")

    if keep:
        kept = 0
        deleted = 0
        for f in list(out_dir.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(out_dir).as_posix()
            base = f.name
            if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(base, pat) for pat in keep):
                kept += 1
            else:
                f.unlink()
                deleted += 1
        # Remove empty directories
        for d in sorted(out_dir.rglob("*"), key=lambda p: -len(p.parts)):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        print(f"Filter '{keep}' applied: kept {kept} file(s), deleted {deleted}")

    print(f"Files in {out_dir}:")
    for f in sorted(out_dir.rglob("*")):
        if f.is_file():
            size_mb = f.stat().st_size / 1e6
            print(f"  {size_mb:>7.2f} MB  {f.relative_to(out_dir)}")


def cmd_run(stage: str, keep: list[str] | None = None) -> None:
    cmd_push(stage)
    print("\nPolling Kaggle for completion (Ctrl+C only stops polling — the kernel keeps running).")
    final_status = cmd_status(stage, follow=True)
    if final_status == "complete":
        cmd_output(stage, keep=keep)
    else:
        sys.exit(f"\nKernel finished with status '{final_status}'. Not downloading output.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("verify", help="confirm the kaggle CLI + auth work")
    for c, h in [
        ("push", "upload notebook to Kaggle (don't wait)"),
        ("status", "one-shot status check"),
        ("output", "download outputs of a finished kernel"),
        ("run", "push + poll + download in one shot"),
    ]:
        sp = sub.add_parser(c, help=h)
        sp.add_argument("stage", help="folder name under kaggle/, e.g. 01_dataset_assembly")
        if c in {"output", "run"}:
            sp.add_argument(
                "--keep",
                nargs="+",
                default=None,
                help=(
                    "fnmatch-style patterns; only files matching at least one are kept "
                    "after download. Example: --keep '*.csv' '*.json' '*.png'"
                ),
            )

    args = ap.parse_args()
    {
        "verify": lambda: cmd_verify(),
        "push": lambda: cmd_push(args.stage),
        "status": lambda: cmd_status(args.stage, follow=False),
        "output": lambda: cmd_output(args.stage, keep=getattr(args, "keep", None)),
        "run": lambda: cmd_run(args.stage, keep=getattr(args, "keep", None)),
    }[args.cmd]()


if __name__ == "__main__":
    main()
