"""Enumerate the top-level class folders of a Kaggle dataset (paginated),
without downloading the data. Used to confirm crop coverage of the big
Indian-crops aggregate before committing to a large download.
"""
from __future__ import annotations

import sys
from collections import Counter

from kaggle import api as k

SLUG = sys.argv[1] if len(sys.argv) > 1 else "hritik2004/indian-crops-leaf-disease"


def main() -> None:
    k.authenticate()
    folders: Counter[str] = Counter()
    token = None
    pages = 0
    while True:
        try:
            res = k.dataset_list_files(SLUG, page_token=token, page_size=200) if token \
                else k.dataset_list_files(SLUG, page_size=200)
        except TypeError:
            res = k.dataset_list_files(SLUG)  # older signature
        files = getattr(res, "files", None) or []
        for f in files:
            name = getattr(f, "name", None) or getattr(f, "path", None) or str(f)
            top = name.replace("\\", "/").split("/")[0]
            if top not in folders:
                print(f"  NEW FOLDER: {top}", flush=True)
            folders[top] += 1
        token = getattr(res, "next_page_token", None) or getattr(res, "nextPageToken", None)
        pages += 1
        if pages % 10 == 0:
            print(f"...{pages} pages, {len(folders)} folders so far", flush=True)
        if not token or pages > 600:
            break
    print(f"\n=== {SLUG} : {len(folders)} top-level folders, {pages} pages ===")
    for name, n in sorted(folders.items()):
        print(f"  {n:7d}  {name}")


if __name__ == "__main__":
    main()
