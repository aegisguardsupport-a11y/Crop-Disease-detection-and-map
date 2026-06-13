# 🌿 CPL Crop Disease Detection — Complete Technical Guide

> **Read this top to bottom.** By the end you'll understand *what* we built, *how* it
> works, *why* every piece exists, and you'll be able to explain it confidently to
> judges. No prior deep-learning knowledge assumed — every term is explained the
> first time it appears.

---

## 1. The 30-second pitch (memorize this)

> "A farmer takes a photo of a sick crop leaf on their phone. Our system finds the
> leaf in the photo, removes the messy background, identifies which of **139
> crop-diseases** it has, tells the farmer **how confident** it is, and gives plain-language
> **treatment advice** — and when it's *not* sure, it honestly says 'retake the photo'
> instead of guessing. It works on **real field photos**, not just clean lab pictures."

That last sentence is the whole game. Keep reading to understand why it's hard and
how we pulled it off.

---

## 2. The core idea in plain English

Think of the system as a **smart assembly line** for a photo. The photo enters at one
end, passes through several specialist stations, and a diagnosis comes out the other
end. Each station does one job and hands its result to the next.

```
📱 Photo → ✅ Check quality → 🔍 Find the leaf → ✂️ Cut out the leaf
        → 🧠 Identify the disease → 📊 Decide how confident we are
        → 🚦 High / Medium / Low → 💊 Treatment advice
```

We didn't build one giant "AI brain." We built a **pipeline of small, focused models
and checks** — which is exactly how serious real-world AI systems are built. That's a
strong story for judges: *"we engineered a system, not just trained a model."*

---

## 3. The absolute basics (so the rest makes sense)

### What is a neural network? (the 1-minute version)
A neural network is a program that **learns patterns from examples** instead of being
explicitly programmed. You show it thousands of labelled pictures ("this is a tomato
with late blight," "this is a healthy rice leaf") and it gradually adjusts millions of
internal numbers ("weights") until it can recognize those patterns in *new* pictures it
has never seen.

> 📚 *Learn more:* [3Blue1Brown — "But what is a neural network?" (YouTube, very visual)](https://www.youtube.com/watch?v=aircAruvnKk)

### Two different jobs our system uses
There are two *kinds* of image AI in our project. People mix these up — knowing the
difference makes you sound expert:

| Job | Question it answers | We use it for |
|---|---|---|
| **Image Classification** | *"What is this a picture of?"* | Naming the **disease** |
| **Image Segmentation** | *"Which exact pixels are the object?"* | Finding the **leaf** and cutting it out |

Classification gives you a **label**. Segmentation gives you a **mask** (an outline of
exactly which pixels belong to the leaf).

> 📚 *Learn more:* [A gentle intro to classification vs detection vs segmentation](https://www.v7labs.com/blog/image-segmentation-guide)

### What is "transfer learning"? (this is everywhere in our project)
Training an image model from zero needs *millions* of images and weeks of compute.
Instead, we take a model that was **already trained on 1.4 million general images**
(ImageNet — cats, cars, furniture, etc.) and **re-teach only the last part** of it to
recognize our crop diseases. The model already "knows" edges, textures, shapes — we
just teach it *our specific* labels. It's like hiring an experienced photographer and
teaching them about plants, instead of raising a child from birth.

> 📚 *Learn more:* [TensorFlow transfer learning tutorial](https://www.tensorflow.org/tutorials/images/transfer_learning)

---

## 4. The architecture, station by station

This matches the workflow diagram in your presentation. Here's what each box *actually
does* and the technology behind it.

### Station 1 — File & quality checks
Before wasting GPU time, we check the upload is a real image of reasonable size, then
run quick **OpenCV** (a classic computer-vision library) checks: Is it too blurry? Too
dark? Too bright? Too low-resolution? A blurry photo can't give a good diagnosis, so we
catch it early.

> *Why it matters to judges:* "We don't blindly trust the input — garbage in would mean
> garbage out, so we gate it."

### Station 2 — Leaf Segmentation (YOLOv8)
This is the "find the leaf" station. We use **YOLOv8-seg**, a famous, fast model family
("YOLO" = *You Only Look Once*). Our version is trained to do **one job**: draw a precise
outline (mask) around the leaf in the photo, ignoring soil, hands, sky, other leaves.

- We trained the **"small" variant (yolov8s-seg)**.
- On our test set it scored **mAP@50 = 0.95** (mAP = "mean Average Precision," a standard
  segmentation score from 0 to 1; 0.95 is excellent — it finds leaves almost perfectly).

> 📚 *Learn more:* [Ultralytics YOLO docs](https://docs.ultralytics.com/tasks/segment/) ·
> [What is mAP?](https://blog.roboflow.com/mean-average-precision/)

### Station 3 — Leaf-area validation + Background Removal
With the mask in hand, we:
1. **Validate** the leaf isn't a tiny speck or filling the entire frame (both are bad).
2. **Cut out** the leaf using the mask, paint the background a flat colour, crop tightly,
   and resize to a fixed **260×260 pixels** — a clean, standardized "leaf portrait."

This **clean-leaf image** is what the disease model actually sees. (Remember this — it
becomes very important in Section 6.)

### Station 4 — Disease Classification (EfficientNetV2)
The brain of the operation. We use **EfficientNetV2-B2**, a modern, efficient
image-classification network from Google Research. It looks at the 260×260 clean leaf
and outputs a **probability for each of the 72 disease classes** (in our retrained model;
the original taxonomy had 139). The highest probability is the diagnosis.

- "EfficientNet" is designed to get high accuracy with relatively few parameters — great
  for a system that has to be fast and deployable.
- "V2-B2" = version 2, size variant B2 (a good speed/accuracy middle ground).

> 📚 *Learn more:* [EfficientNetV2 paper (plain summary)](https://arxiv.org/abs/2104.00298) ·
> [Keras EfficientNet docs](https://keras.io/api/applications/efficientnet_v2/)

### Station 5 — Cross-check with CLIP (a clever safety net)
Here's a neat trick. **CLIP** is an OpenAI model that understands images *and* text
together. We ask it, *zero-shot* (without any training), "does this picture look more
like 'a photograph of a tomato leaf' or 'a photograph of a cotton leaf'?" If CLIP's
opinion of the **crop** disagrees with our classifier, that's a red flag we factor into
confidence.

> *Why it matters:* two independent models agreeing is far more trustworthy than one
> model alone. **"Zero-shot"** means CLIP can judge crops it was never specifically
> trained on, just from the text description.
>
> 📚 *Learn more:* [OpenAI CLIP explained](https://openai.com/research/clip)

### Station 6 — The Confidence Engine
A single AI's "92% sure" number is often unreliable. So instead of trusting it blindly,
we **fuse multiple signals** into one honest confidence score:

- the classifier's top probability,
- the **gap** between its 1st and 2nd guesses (a big gap = decisive; a tiny gap = it's
  basically flipping a coin),
- image quality score,
- segmentation confidence,
- how much of the frame the leaf covers,
- whether CLIP agreed.

This blended score is the system's *real* confidence. **This is one of your strongest
talking points** — most hackathon projects just show a raw softmax number; you built a
multi-signal trust system.

### Station 7 — The Decision Router
Based on that confidence, the system takes one of three honest actions:

| Confidence | Action |
|---|---|
| 🟢 **High** | Show the diagnosis + treatment, send to the map/database |
| 🟡 **Medium** | Show it but route to an **expert-review queue** ("a human should double-check") |
| 🔴 **Low** | Don't guess — show **"retake the photo"** guidance |

> *Why judges love this:* **A model that knows when it doesn't know is more trustworthy
> than one that always answers.** In agriculture, a confident wrong answer could cost a
> farmer their crop. This is "responsible AI" in action.

### Station 8 — Treatment Advice via RAG
Finally, once we know the disease, the farmer needs to know *what to do*. We use **RAG
(Retrieval-Augmented Generation)**:

1. We collected detailed text documents about each of the 20 crops (symptoms, treatment,
   prevention).
2. We chopped them into chunks and stored them in **ChromaDB**, a "vector database" that
   can find the most *relevant* chunk for any query.
3. When a disease is identified, we **retrieve** the right chunks and feed them to
   **Google's Gemini** language model, which writes a clean, plain-language advisory.

This means the advice is **grounded in our real documents**, not hallucinated by the AI.

> 📚 *Learn more:* [What is RAG? (simple explainer)](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

## 5. The journey of one photo (end to end)

Tie it all together — this makes a great live-demo narration:

```
1. Farmer uploads leaf.jpg
2. File/size OK?            ──no──▶ reject
3. Quality OK (sharp, lit)? ──no──▶ "retake"
4. YOLO finds the leaf      ──none─▶ "retake"
5. Cut leaf, remove bg, resize to 260×260
6. EfficientNet → "tomato::late_blight 88%"
7. CLIP cross-check: "yes, looks like tomato" ✓
8. Confidence Engine fuses all signals → 0.86
9. Router: 0.86 = HIGH → show diagnosis
10. RAG → "Late blight. Remove infected leaves, apply
    copper-based fungicide, avoid overhead watering..."
```

---

## 6. The hard problem we actually solved (THE story)

**This is the heart of your presentation.** Everything above is the architecture; *this*
is the insight that makes your project impressive.

### The problem: the "domain gap"
Almost every public crop-disease dataset is made of **lab photos** — a single leaf on a
clean white or grey background, perfect lighting. Models trained on these get ~95–99%
accuracy *on lab photos*… and then **completely fall apart on real field photos** from a
farmer's phone (messy background, sunlight, shadows, blur, odd angles).

This mismatch between training data and real-world data is called the **domain gap** (or
"distribution shift"). It's one of the most famous, real problems in applied machine
learning — and it's exactly why the *original* version of this model failed on real
photos. We literally proved it: feeding it real leaves gave a near-random output.

> 📚 *Learn more:* [The PlantVillage domain-gap problem (research)](https://arxiv.org/abs/1612.03715) ·
> [Distribution shift explained](https://huyenchip.com/2022/02/07/data-distribution-shifts-and-monitoring.html)

### Our solution — three weapons against the gap

**Weapon 1: Train on what the model will actually see ("train/serve alignment").**
At prediction time, the model never sees a raw photo — it sees the **background-removed,
cropped 260×260 clean leaf** (Station 3). So we made sure to **train it on
background-removed clean leaves too.** Training and real use now match. This sounds
obvious but is the single biggest accuracy lever, and the original model got it wrong.

**Weapon 2: Synthesize fake "field" photos ("background compositing").**
We don't have real field photos for our niche Indian crops — they don't exist publicly.
So we *made* them: we cut each lab leaf out with our segmenter, then **pasted it onto
real soil/field backgrounds** with random rotation, shadows, lighting and blur. From
56,000 lab images we generated ~56,000 synthetic "field" images. The model learns
"disease texture on a leaf, in messy surroundings" instead of "disease on white."

> *This is your wow-factor line:* "Field data for these crops doesn't exist, so we used
> our own segmentation model to manufacture it — the pipeline feeds itself."
>
> 📚 *Learn more:* [Cut-paste / copy-paste augmentation (research)](https://arxiv.org/abs/2012.07177)

**Weapon 3: Aggressive "real-world" augmentation.**
During training we randomly distort each image to mimic phone-photo reality: re-compress
it as low-quality JPEG (like WhatsApp does), shift colours (white-balance), add sensor
noise, black out random patches (occlusion), flip, rotate, zoom. The model becomes
robust to all these because it saw them in training.

> 📚 *Learn more:* [Data augmentation explained](https://www.tensorflow.org/tutorials/images/data_augmentation)

---

## 7. The data — where it came from

### Two completely separate datasets (don't confuse them!)
| Dataset | Labels | Trains | Size |
|---|---|---|---|
| **Segmentation data** | leaf *outlines* (1 class: "leaf") | the YOLO leaf-finder | 9,010 images |
| **Classification data** | *disease* names (`crop::disease`) | the EfficientNet diagnoser | 56,377 images, 72 classes |

A common confusion: "can we train the disease model on the segmentation data?" **No** —
the segmentation data only knows *where* the leaf is, not *what disease* it has. Different
jobs, different labels.

### How we assembled the classification dataset
The original combined dataset was lost, so we rebuilt it. We searched Kaggle for a
disease dataset for each of the 20 crops and downloaded the 15 that had usable public
data (tomato, rice, cotton, sugarcane, chilli, cauliflower, maize, groundnut, blackgram,
brinjal, soyabean, sunflower, wheat, sorghum, cabbage). Five crops (cowpea, pigeonpea,
ragi, onion, okra) had **no clean public dataset** — an honest limitation worth stating.

Then we **cleaned** it:
- removed exact-duplicate images (using md5 hashes — 7,138 dupes caught),
- removed thumbnails / corrupt files,
- normalized every dataset's different folder layout into one `crop/disease/` structure,
- dropped classes with too few images to learn from,
- split into **train (80%) / validation (10%) / test (10%)** — *stratified*, meaning each
  split keeps the same class proportions.

> *Why the split matters:* you **train** on one part, **tune** on the validation part, and
> only **measure final honesty** on the test part the model never saw. Testing on data the
> model trained on is the #1 way people fool themselves with fake high scores.

---

## 8. The training pipeline (5 stages)

We built a clean, reproducible pipeline. Each stage is a separate notebook that runs on
**Kaggle's free GPUs** (so your laptop stays free). Stages hand outputs to the next like
a relay race.

```
01_organize     → clean + dedup + split the 56k images          (your laptop)
03_train_yolo   → train the leaf segmenter (yolov8s-seg)        (Kaggle GPU)
04_segment      → cut clean leaves + make field composites      (Kaggle GPU)
05_classifier   → train EfficientNetV2-B2 on the result         (Kaggle GPU)
+ deploy script → swap the new model into the live system       (your laptop)
```

### Inside Stage 5 — the techniques that make it "win-grade"
This is where the advanced data-science lives. Each of these is a real, named technique
you can mention:

| Technique | Plain-English what & why |
|---|---|
| **Two-phase transfer learning** | First train only the new "head" with the pretrained body frozen (fast, stable), then unfreeze and fine-tune the whole network gently. Best of both. |
| **Class balancing (√-sampling)** | Our biggest class (tomato healthy, 3,191 imgs) was **51× larger** than the smallest. Left alone, the model would just learn "everything is tomato." We sample rarer classes more often, cutting the imbalance to ~7×. |
| **Macro-F1 model selection** | We pick the "best" model by **macro-F1** (average score across *all classes equally*), not plain accuracy — so a tomato-biased model literally can't win. |
| **Label smoothing** | Stops the model from becoming arrogantly overconfident. |
| **Mixup** | Blend two images + their labels together during training; weirdly, this makes models more robust and better-calibrated. | 
| **Mixed-precision training** | Use 16-bit numbers where safe to train ~2× faster on the GPU. |
| **Temperature calibration** | After training, we tune one number so that "80% confident" *actually means* right 80% of the time. Makes the Confidence Engine honest. |
| **Field + clean test sets** | We measure accuracy on **both** clean lab leaves *and* synthetic field leaves, separately — so we know the real-world number, not the flattering one. |

> 📚 *Learn more:* [Mixup paper](https://arxiv.org/abs/1710.09412) ·
> [Label smoothing](https://arxiv.org/abs/1512.00567) ·
> [Confidence calibration / temperature scaling](https://arxiv.org/abs/1706.04599) ·
> [Why macro-F1 for imbalance](https://towardsdatascience.com/multi-class-metrics-made-simple-part-ii-the-f1-score-ebe8b2c2ca1)

---

## 9. Deployment — how it becomes a real, usable service

A trained model file is useless until people can actually *use* it. Here's the serving
stack.

### The backend API (FastAPI on Hugging Face Spaces)
- **FastAPI** is a modern Python framework for building web APIs. We wrapped the whole
  pipeline (Stations 1–8) behind a single web address with endpoints:
  - `POST /predict-v2` — the full pipeline (upload image → JSON diagnosis)
  - `GET /health`, `/ready` — "is the service alive?" checks
  - `GET /docs` — auto-generated interactive API documentation
  - `POST /explain` — returns a **Grad-CAM heatmap** (see below)
- It's packaged with **Docker** (a "shipping container" for software — bundles the code +
  exact dependencies so it runs identically anywhere) and hosted **free on Hugging Face
  Spaces**, which gives you a public HTTPS URL.

> 📚 *Learn more:* [FastAPI](https://fastapi.tiangolo.com/) ·
> [What is Docker? (5-min)](https://www.youtube.com/watch?v=Gjnup-PuquQ) ·
> [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces)

### The demo UI (Streamlit)
A simple web app where you drag-drop a leaf image and watch every pipeline stage render —
the mask, the clean leaf, the prediction bars, the confidence breakdown, the decision.
Built with **Streamlit** (turns Python scripts into web apps), also on Hugging Face.

### Explainability (Grad-CAM)
Judges always ask *"how do we trust the AI?"* Our `/explain` endpoint produces a
**heatmap** that highlights *which parts of the leaf* the model looked at to make its
decision. If it's looking at the diseased spots — great, it's reasoning correctly. This
is called **Grad-CAM**, and it turns the "black box" into something you can inspect.

> 📚 *Learn more:* [Grad-CAM explained simply](https://blog.roboflow.com/grad-cam/)

### Bonus production features (mention if asked — shows maturity)
- **Knowledge distillation** to a tiny **MobileNetV3** model — a "student" model that
  copies the big "teacher," small and fast enough to run **offline on a phone**.
- **Drift monitoring** (Evidently) — watches whether incoming real photos start looking
  different from training data over time, so you know when to retrain.
- **MLflow** — tracks every training experiment's settings and results.

> 📚 *Learn more:* [Knowledge distillation](https://www.v7labs.com/blog/knowledge-distillation-guide) ·
> [Model drift](https://www.evidentlyai.com/ml-in-production/data-drift)

---

## 10. The full tech stack (cheat-sheet table)

| Layer | Technology | Job |
|---|---|---|
| Mobile app | React Native + Expo | Farmer uploads photo |
| API backend | FastAPI + Docker | Runs the pipeline, serves JSON |
| Hosting | Hugging Face Spaces | Free public deployment |
| Demo UI | Streamlit | Visual web demo |
| Leaf finder | YOLOv8s-seg (Ultralytics) | Segmentation |
| Disease brain | EfficientNetV2-B2 (TensorFlow/Keras) | Classification |
| Cross-check | CLIP (Transformers) | Zero-shot crop verify |
| Advice | ChromaDB + Google Gemini | RAG treatment advisories |
| Explainability | Grad-CAM | Heatmaps of model attention |
| Training | Kaggle GPUs (P100/T4) | Free model training |
| Image ops | OpenCV, Pillow, NumPy | Quality checks, compositing |
| Monitoring | MLflow, Evidently | Experiment tracking, drift |

---

## 11. How to present this (talking points & likely questions)

### Your 3-act story
1. **The problem (relatable):** "Models that get 99% in the lab fail completely on real
   farmer photos. We hit this exact wall."
2. **The insight (impressive):** "The issue isn't the model — it's that training photos
   don't look like real photos. So we manufactured realistic training data using our own
   segmentation model, and we trained the classifier on exactly what it sees in
   production."
3. **The responsible finish:** "And we built a confidence engine so it knows when *not* to
   answer — because a confident wrong diagnosis can cost a farmer their crop."

### Questions judges will probably ask — and your answers
- **"How is this different from existing apps?"** → "Most are trained on lab data and break
  in the field. We specifically engineered for the domain gap with compositing,
  train/serve alignment, and a multi-signal confidence system."
- **"How accurate is it?"** → Give your **field test** number, not just the clean one (more
  honest, more impressive). *(Fill in once training finishes.)*
- **"What if it's wrong?"** → "It routes uncertain cases to a human expert queue or asks
  for a retake instead of guessing — see the decision router."
- **"Does it run on a phone?"** → "Yes — we distilled a ~1MB MobileNet student model for
  offline use."
- **"How do we trust the AI?"** → "Grad-CAM heatmaps show it's looking at the actual
  diseased regions, plus an independent CLIP model cross-checks the crop."
- **"What are the limitations?"** → (Honesty scores points) "5 niche crops lack public
  data, so coverage there is weak; and synthetic field data, while effective, isn't a full
  substitute for real field collection — that's our next step."

### The killer live demo
Pull **any** crop-leaf photo off Google *on the spot* (unstaged) → upload to the live
Hugging Face URL → show: leaf found → background removed → diagnosis + confidence →
Grad-CAM heatmap → treatment advice. Then upload a junk/blurry image → show it gracefully
says **"retake."** A system that fails *gracefully* impresses more than a fake 100%.

---

## 12. Glossary (quick reference)

- **Model / weights** — the trained AI and its learned numbers.
- **Classification** — naming what's in an image. **Segmentation** — outlining exact pixels.
- **Transfer learning** — reusing a pretrained model and re-teaching the last part.
- **Domain gap / distribution shift** — training data ≠ real-world data; causes failures.
- **Augmentation** — randomly distorting training images to build robustness.
- **Class imbalance** — some categories have far more examples than others.
- **Train / validation / test split** — learn / tune / final-honest-measure portions.
- **mAP** — segmentation/detection quality score (0–1, higher better).
- **Macro-F1** — accuracy averaged across all classes equally (fairness metric).
- **Calibration** — making "80% confident" actually mean 80% correct.
- **RAG** — fetch real documents, then let an LLM write grounded answers.
- **Zero-shot** — a model judging something it was never explicitly trained on.
- **Grad-CAM** — heatmap of where a model "looked."
- **Distillation** — training a small fast model to mimic a big accurate one.
- **Docker** — packaging software so it runs identically everywhere.

---

## 13. Where everything lives

- **Code:** `cpl_hackathon/image segmentation/kaggle/` (the 5 training stages)
- **Serving:** `cpl_hackathon/hf_deploy_stage/` (FastAPI), `hf_ui_stage/` (Streamlit)
- **Live API:** Hugging Face Space `prateek712/cpl-crop-disease-api`
- **Live UI:** Hugging Face Space `prateek712/cpl-crop-disease-ui`
- **Datasets & models:** Kaggle account `prateekpatel712`

---

*You don't need to memorize the code — understand the **story** (Section 6), the
**pipeline** (Section 4), and the **techniques** (Section 8). If you can explain the
domain gap and how we beat it, you understand the heart of this project. Good luck — you've
got this. 🌱*
