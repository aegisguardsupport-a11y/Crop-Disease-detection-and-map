# 🌿 CPL Crop Doctor — Offline Model Kit

**A drop-in package to run crop-disease detection fully offline in a React Native (Expo) app.**

Hand this folder to your app developer. It contains the AI model, the
treatment data, all the non-AI pipeline logic (already written + type-checked),
and a step-by-step integration guide. No server, no internet required at run time.

---

## What this does
A farmer photographs a crop leaf → the app runs everything **on the phone** →
returns the disease, a confidence level, an honest "high / review / retake"
decision, and plain-language treatment advice. Works with no signal.

It is a compact, on-device copy of our server model (a *student* trained to
mimic the larger *teacher*). It covers **15 crops / 72 disease classes**.

---

## 📦 What's in this kit

```
cpl_offline_kit/
├── models/
│   ├── cpl_student_int8.tflite     # THE model (~1–3 MB, int8). The app loads this.
│   ├── cpl_student_float.tflite    # fallback (larger, float). Use if int8 misbehaves.
│   ├── labels.json                 # class index (0..71) -> "crop::disease"
│   └── preprocessing.json          # exact input contract (size, pixel range)
├── data/
│   └── advisories.json             # offline treatment advice, keyed by label
├── pipeline/                       # pure TypeScript, no native deps, type-checked ✅
│   ├── types.ts                    # shared types (the contract)
│   ├── quality.ts                  # image quality gate (blur/brightness/contrast)
│   ├── confidence.ts               # multi-signal confidence engine
│   ├── router.ts                   # high / expert-review / retake decision
│   ├── index.ts                    # ⭐ runDiagnosis() — the one function to call
│   └── classifier.example.ts       # how to run the .tflite (the only native bit)
├── README.md                       # this file
└── INTEGRATION_GUIDE.md            # ⭐ step-by-step Expo setup
```

---

## 🧠 How it works (the pipeline)

```
 camera photo
     │
     ▼
 [1] quality.ts        → too blurry/dark/small?  → "retake"
     │ (ok)
     ▼
 [2] classifier.tflite → 72 disease probabilities   ← THE model (on-device)
     │
     ▼
 [3] confidence.ts     → fuse top-1, gap, quality → one 0..1 score
     │
     ▼
 [4] router.ts         → high_confidence / expert_review / retake
     │
     ▼
 [5] advisories.json   → look up treatment advice by predicted label
```

Steps 1, 3, 4, 5 are **pure TypeScript in this kit** — already written and
type-checked. Step 2 (running the model) is the only native piece, and
`classifier.example.ts` shows exactly how.

`runDiagnosis()` in `index.ts` wires 1→3→4→5 together. You feed it the model's
output from step 2; it returns the full result.

---

## 🎚️ ⚠️ Segmentation is REQUIRED (not optional)

We tested this carefully: the classifier was trained on **background-removed
leaves**, so if you feed it a **raw photo** it returns garbage. You **must**
run leaf segmentation (background removal) BEFORE the classifier — on a clean
in-crop leaf it works well; on a raw photo it does not.

**What this means for the offline app:** you need an on-device leaf segmenter
(YOLOv8-seg) as step 1. That is the hard part of mobile ML. See the
"Segmentation" section in `INTEGRATION_GUIDE.md`.

> 💡 **Strongly recommended — hybrid:** if the phone has signal, call our
> online API (full accuracy + live advice + segmentation done server-side); if
> offline, use this on-device model. The hybrid avoids the hardest mobile work
> for the common (online) case and still works with no signal.

> 💡 **Best of both — hybrid:** if the phone has signal, call our online API
> (full accuracy + live Gemini advice); if offline, use this on-device model.
> The app always gives an answer; quality scales with connectivity.

---

## 📊 Model performance (measured)

| Metric | Teacher (server) | **Student (this kit, float)** |
|---|---|---|
| Clean-image top-1 | 97.7% | **81.5%** |
| Field-image top-1 | 89.9% | **72.4%** |
| Field-image **top-3** | 95.0% | **87.1%** |
| Size (float TFLite) | ~30 MB | **1.15 MB** |
| Params | ~8.8 M | **0.98 M** |
| Speed (mid Android, NN accel) | server | **~10–20 ms** |

> The correct disease is in the **top-3 about 87% of the time** on field-style
> images — so **show the top-3** in your UI, not just the top-1. Use the FLOAT
> model (`cpl_student_float.tflite`); int8 is included but measurably less
> accurate on this task.

---

## ⚠️ Honest limitations (please read)
- This is a **compressed** model — a few % less accurate than the server.
- **19 of 72 diseases** have a generic advisory (no detailed doc yet); the app
  shows an honest "consult an expert" message for those. The other 53 give full advice.
- It is a **closed-world** classifier — it will guess *some* disease for any leaf
  photo. The confidence engine + "retake/expert-review" routing are what keep it
  honest; **always show the confidence level to the user.**
- No live Gemini advice offline — advice is the pre-written text in `advisories.json`.

---

## ▶️ Start here
Open **`INTEGRATION_GUIDE.md`** for the full step-by-step setup.
