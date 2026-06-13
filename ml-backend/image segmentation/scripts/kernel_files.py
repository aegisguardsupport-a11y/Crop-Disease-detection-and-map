"""Download specific files from a Kaggle kernel's output, paginating properly.

The kaggle 1.8.4 ``kernels_output`` only returns the first page (~20 files) and
silently ignores the rest. This wrapper paginates ``list_kernel_session_output``
and downloads each matching file with ``requests``.

Usage:
    python scripts/kernel_files.py user/slug \\
        --pattern "(manifest\\.csv|summary\\.json|preview_grid\\.png)$" \\
        --out outputs/01_dataset_assembly
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kernel", help="user/slug")
    ap.add_argument("--pattern", required=True, help="regex applied to file_name (re.search)")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--max-bytes", type=int, default=10_000_000, help="skip files bigger than this")
    args = ap.parse_args()

    import requests
    from kaggle import api as kapi
    from kaggle.api.kaggle_api_extended import ApiListKernelSessionOutputRequest

    kapi.authenticate()
    pattern = re.compile(args.pattern)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    user, slug = args.kernel.split("/", 1)
    matched: list[tuple[str, str, int]] = []  # (name, url, size)
    token: str | None = None
    pages = 0

    with kapi.build_kaggle_client() as client:
        api_client = client.kernels.kernels_api_client
        while True:
            req = ApiListKernelSessionOutputRequest()
            req.user_name = user
            req.kernel_slug = slug
            if token:
                req.page_token = token
            resp = api_client.list_kernel_session_output(req)
            pages += 1
            for f in resp.files:
                name = getattr(f, "file_name", "") or getattr(f, "name", "")
                size = int(getattr(f, "size", 0) or 0)
                url = getattr(f, "url", "") or ""
                if pattern.search(name):
                    matched.append((name, url, size))
            token = getattr(resp, "next_page_token", None) or None
            if not token:
                break

    print(f"Pages scanned: {pages}; files matching {args.pattern!r}: {len(matched)}")
    for name, _url, size in matched:
        print(f"  {size:>10}  {name}")

    print()
    downloaded = 0
    for name, url, size in matched:
        if size and size > args.max_bytes:
            print(f"SKIP {name} (size {size} > max-bytes {args.max_bytes})")
            continue
        if not url:
            print(f"SKIP {name} (no URL in response)")
            continue
        out_file = out / Path(name).name  # flatten any subdir prefix
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        out_file.write_bytes(r.content)
        print(f"Saved {out_file} ({out_file.stat().st_size} bytes)")
        downloaded += 1

    print(f"\nDone. {downloaded}/{len(matched)} files downloaded to {out}")


if __name__ == "__main__":
    main()
