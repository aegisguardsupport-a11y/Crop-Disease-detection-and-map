"""List all output files of a Kaggle kernel (paginated). Stand-alone diagnostic."""

from __future__ import annotations

import argparse
import os

os.environ.setdefault("PYTHONUTF8", "1")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("kernel", help="user/slug")
    ap.add_argument("--ext", nargs="+", default=None, help="filter by extensions, e.g. csv json png")
    args = ap.parse_args()

    from kaggle import api as k

    k.authenticate()

    all_files = []
    token = None
    while True:
        if token:
            resp = k.kernels_list_files(args.kernel, page_token=token)
        else:
            resp = k.kernels_list_files(args.kernel)
        all_files.extend(resp.files)
        token = getattr(resp, "next_page_token", None) or getattr(resp, "nextPageToken", None)
        if not token:
            break

    print(f"Total files: {len(all_files)}")
    ext_count: dict[str, int] = {}
    for f in all_files:
        name = getattr(f, "name", "")
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else "(none)"
        ext_count[ext] = ext_count.get(ext, 0) + 1
    print("By extension:")
    for ext, n in sorted(ext_count.items(), key=lambda x: -x[1])[:15]:
        print(f"  {n:>6}  .{ext}")

    if args.ext:
        targets = tuple("." + e.lower() for e in args.ext)
        matches = [f for f in all_files if getattr(f, "name", "").lower().endswith(targets)]
        print(f"\nFiles matching {args.ext}: {len(matches)}")
        for f in matches:
            size = getattr(f, "size", "?")
            print(f"  {size!s:>12}  {getattr(f, 'name', '?')}")


if __name__ == "__main__":
    main()
