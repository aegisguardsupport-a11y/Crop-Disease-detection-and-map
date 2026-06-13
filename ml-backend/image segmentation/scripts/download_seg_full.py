"""Paginated + parallel downloader for a Kaggle kernel's full output.

kaggle 2.2.1's `kernels_output` only fetches the first page (~500 files) and
never follows next_page_token, so label files never download. This walks every
page (sequential listing) and downloads each page's files concurrently. It
resumes — files already on disk (non-empty) are skipped instantly.
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from kaggle import api as k  # the KaggleApi *instance*

OWNER = "prateekpatel712"
SLUG = "cpl-02-sam-autolabel"
DEST = r"C:\Users\techb\OneDrive\Desktop\cpl_hackathon\image segmentation\outputs\02_sam_autolabel"
WORKERS = 24


def fetch(item) -> str:
    outfile = os.path.join(DEST, item.file_name)
    if os.path.exists(outfile) and os.path.getsize(outfile) > 0:
        return "skip"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    try:
        r = requests.get(item.url, timeout=60)
        r.raise_for_status()
        with open(outfile, "wb") as out:
            out.write(r.content)
        return "ok"
    except Exception as e:  # noqa: BLE001
        print(f"  ERR {item.file_name}: {e}", flush=True)
        return "err"


def main() -> None:
    k.authenticate()
    ext = sys.modules[type(k).__module__]
    ReqCls = ext.ApiListKernelSessionOutputRequest

    os.makedirs(DEST, exist_ok=True)
    got = skipped = errors = pages = 0
    token = None
    t0 = time.time()

    with k.build_kaggle_client() as client:
        while True:
            req = ReqCls()
            req.user_name = OWNER
            req.kernel_slug = SLUG
            if token:
                req.page_token = token
            resp = client.kernels.kernels_api_client.list_kernel_session_output(req)
            pages += 1
            files = list(resp.files or [])
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                for res in pool.map(fetch, files):
                    if res == "ok":
                        got += 1
                    elif res == "skip":
                        skipped += 1
                    else:
                        errors += 1
            print(
                f"page {pages:>3} | downloaded={got} skipped={skipped} errors={errors} "
                f"| {time.time()-t0:5.0f}s",
                flush=True,
            )
            token = resp.next_page_token
            if not token:
                break

    print(f"DONE: downloaded={got} skipped={skipped} errors={errors} pages={pages}")


if __name__ == "__main__":
    sys.exit(main())
