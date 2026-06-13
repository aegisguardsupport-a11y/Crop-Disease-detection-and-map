# Deploying to Hugging Face Spaces

End-to-end walkthrough to publish the CPL Crop Disease API as a public Hugging Face Space.
Once deployed your teammates can hit `https://prateek712-cpl-crop-disease-api.hf.space/predict-v2` from any frontend.

---

## 0. Prerequisites (one-time)

1. **HF account** — sign up at <https://huggingface.co/join> if you don't have one.
2. **HF write token** — <https://huggingface.co/settings/tokens> → *New token* → role **Write** → copy it.
3. **Git LFS** — required to push the model weights:

   - Windows: download <https://git-lfs.com/> and run the installer
   - Then in any shell: `git lfs install`

4. **Verify everything**:

   ```powershell
   git --version
   git lfs version
   huggingface-cli whoami        # may need: pip install huggingface_hub
   ```

---

## 1. Create the Space on the website

1. Go to <https://huggingface.co/new-space>
2. **Owner**: `prateek712`
3. **Space name**: `cpl-crop-disease-api` (or whatever you prefer — this becomes part of the URL)
4. **License**: MIT (or none)
5. **SDK**: **Docker** → choose *Blank* template
6. **Hardware**: *CPU basic — Free*
7. **Visibility**: Public
8. Click **Create Space**

You now have an empty Space at:

```
https://huggingface.co/spaces/prateek712/cpl-crop-disease-api
```

---

## 2. Stage the deploy directory

We don't push the whole project — only the bits the Space needs. The `huggingface/`
folder in this repo holds the Space-specific files (`README.md`, `Dockerfile`,
`.gitattributes`, `requirements.hfspaces.txt`).

From the project root in PowerShell:

```powershell
$ROOT  = "C:\Users\techb\OneDrive\Desktop\cpl_hackathon\Crop_disease_prediction_online"
$STAGE = "C:\Users\techb\OneDrive\Desktop\cpl_hackathon\hf_deploy_stage"
$USER  = "prateek712"
$SPACE = "cpl-crop-disease-api"

# Wipe & recreate the staging dir
if (Test-Path $STAGE) { Remove-Item -Recurse -Force $STAGE }
New-Item -ItemType Directory -Force -Path $STAGE | Out-Null

Set-Location $STAGE

# Clone the empty Space repo (uses HF token via your ~/.huggingface/token or Git creds)
git clone "https://huggingface.co/spaces/$USER/$SPACE" .
git lfs install

# Copy HF-specific files to the Space repo root
Copy-Item "$ROOT\huggingface\README.md"                   ".\README.md" -Force
Copy-Item "$ROOT\huggingface\Dockerfile"                  ".\Dockerfile" -Force
Copy-Item "$ROOT\huggingface\.gitattributes"              ".\.gitattributes" -Force
Copy-Item "$ROOT\huggingface\requirements.hfspaces.txt"   ".\requirements.hfspaces.txt" -Force
Copy-Item "$ROOT\pyproject.toml"                          ".\pyproject.toml" -Force

# Copy code
Copy-Item -Recurse "$ROOT\src"   ".\src"

# Copy the bits of exports/ we actually serve (skip the big .tflite which is unused)
New-Item -ItemType Directory -Force -Path ".\exports" | Out-Null
Copy-Item -Recurse "$ROOT\exports\saved_model"            ".\exports\saved_model"
Copy-Item        "$ROOT\exports\cpl_id_to_label.json"     ".\exports\cpl_id_to_label.json"
Copy-Item        "$ROOT\exports\cpl_preprocessing_config.json" ".\exports\cpl_preprocessing_config.json"

# Copy models/
Copy-Item -Recurse "$ROOT\models" ".\models"

# Optional: copy a sample test image so the Space README has something to demo
New-Item -ItemType Directory -Force -Path ".\samples" | Out-Null
Copy-Item "$ROOT\scripts\wheat_test.jpg" ".\samples\wheat_test.jpg" -ErrorAction SilentlyContinue

# Sanity-check what we're about to push
Get-ChildItem -Recurse | Measure-Object -Property Length -Sum | ForEach-Object {
    "Total size: {0:N1} MB" -f ($_.Sum / 1MB)
}
```

Expected staged size: ~150-200 MB (B2 SavedModel + YOLO + hierarchical bundle).

---

## 3. Push to HF

```powershell
# Tell git who you are (only first time)
git config user.email "<your-email>"
git config user.name  "<your-name>"

# Stage everything; LFS will auto-handle the binary blobs based on .gitattributes
git add .gitattributes
git add .
git status                       # verify the binaries say "Git LFS"

git commit -m "Initial deploy: CPL Crop Disease API"
git push origin main
```

If the push asks for credentials:
- **Username**: your HF username
- **Password**: paste your HF *write token* (NOT your account password)

The push uploads ~150 MB. First push takes 5-15 minutes depending on your connection.

---

## 4. Watch the build

1. Go to <https://huggingface.co/spaces/prateek712/cpl-crop-disease-api>
2. The Space shows **Building...** for ~20-40 minutes (TF + torch + transformers wheels are heavy).
3. When status flips to **Running**, the endpoint is live.

Watch logs with:

```powershell
huggingface-cli space logs prateek712/cpl-crop-disease-api
```

or via the **Logs** tab on the Space page.

---

## 5. Verify the endpoint

```powershell
$URL = "https://prateek712-cpl-crop-disease-api.hf.space"

# Liveness probe
curl.exe "$URL/health"

# Readiness probe (waits until SavedModel + CLIP are loaded — first call after sleep takes 60-120 s)
curl.exe "$URL/ready"

# Run a real prediction
curl.exe -X POST "$URL/predict-v2?topk=3&explain=false" `
    -F "file=@C:\Users\techb\OneDrive\Desktop\cpl_hackathon\Crop_disease_prediction_online\scripts\wheat_test.jpg;type=image/jpeg"
```

You should get back the standard `/predict-v2` JSON response.

---

## 6. Hand the endpoint to your teammates

Copy [`API.md`](./API.md) into a Slack message / Notion page. It contains:

- The endpoint URL
- Request schema (multipart upload, query params)
- Response schema with field-by-field explanations
- A copy-pasteable curl example
- A copy-pasteable JavaScript `fetch` example
- A copy-pasteable Python `httpx` example
- CORS notes
- Rate-limit / sleep behaviour notes

---

## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| `git push` rejected — file too large | LFS not installed or `.gitattributes` not committed first | `git lfs install`, then `git add .gitattributes` *before* `git add .` |
| Build fails with "no space left on device" | Image too big for free tier | Confirm `.dockerignore` excluded venvs; consider `requirements.hfspaces.txt` (already lean) |
| Build takes >40 min and times out | TF or torch wheel install slow | Often transient — click *Restart Space* on the Space page |
| `/predict-v2` returns 503 | YOLO `best.pt` not in image | Verify `models/leaf_seg/best.pt` was committed via LFS |
| First request takes 2 min | Cold start: SavedModel + CLIP loading | Expected on free tier. Subsequent requests are fast. |
| Space sleeps and refuses requests | 48 h of inactivity | Hit `/health` periodically (e.g. UptimeRobot, free) to keep awake |
| CORS error in browser | Frontend on different origin | API is `allow_origins=["*"]` by default — re-deploy if you changed `CPL_CORS_ORIGINS` |

---

## Updating the Space later

```powershell
Set-Location $STAGE
# update files in the staging dir (e.g. recopy from $ROOT)
git add .
git commit -m "<message>"
git push
```

HF will automatically rebuild and redeploy.
