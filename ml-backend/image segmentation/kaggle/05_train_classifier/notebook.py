# %% [markdown]
# # CPL Crop Disease — Stage 5: EfficientNetV2-B2 classifier (field-robust, balanced)
#
# Consumes stage 4 (kernel source `cpl-04-segment-preprocess`):
# `clean/` serving-parity cutouts for all splits, `composite/` field
# composites for all splits (train: random; val/test: deterministic).
#
# ## Design (each choice tied to a deployment-distribution fact)
# - **51x class imbalance** -> sqrt-tempered sampling (p ∝ √n), label
#   smoothing 0.1, NO class weights (no double correction), macro-F1
#   checkpoint selection.
# - **Model selection shift** -> validation = clean-val + field-val (the
#   deterministic composites), so "best checkpoint" = best at both worlds.
# - **Internet photos are recompressed/white-balance-shifted/occluded** ->
#   random JPEG quality 40-95, hue/saturation jitter, cutout (black patches
#   match the background fill), on top of flip/rot/zoom/contrast/brightness.
# - **Long-tail robustness + calibration** -> mixup (alpha 0.2, 50% of
#   batches) + temperature scaling baked into the export.
# - **Large lab->field shift** -> EfficientNetV2-B2, full-backbone fine-tune
#   with cosine LR decay (BN frozen via training=False pattern).
#
# Test reports CLEAN-test and FIELD-test separately; per-crop table for
# bias visibility. Exports keep the FastAPI serving contract unchanged.

# %%
import csv
import json
import math
from pathlib import Path

import numpy as np
import tensorflow as tf

SEED = 42
tf.random.set_seed(SEED)
np.random.seed(SEED)

INPUT_ROOT = Path("/kaggle/input")
OUT = Path("/kaggle/working")
(OUT / "exports").mkdir(parents=True, exist_ok=True)
(OUT / "reports").mkdir(parents=True, exist_ok=True)
(OUT / "models").mkdir(parents=True, exist_ok=True)

IMG = (260, 260)
BATCH = 32
HEAD_EPOCHS = 6
FT_EPOCHS = 14
LR_HEAD = 1e-3
LR_FT = 1e-4
DROPOUT = 0.35
SMOOTH = 0.1
MIXUP_ALPHA = 0.2
MIXUP_PROB = 0.5

gpus = tf.config.list_physical_devices("GPU")
print("GPUs:", gpus)
if gpus:
    tf.keras.mixed_precision.set_global_policy("mixed_float16")

# %% [markdown]
# ## Locate stage-4 output + label map

# %%
manifests = list(INPUT_ROOT.rglob("manifest_clean.csv"))
if not manifests:
    # Kaggle packages very large kernel outputs as a single _output_.zip —
    # extract it to local disk (also faster IO for training than the mount).
    import zipfile
    zips = list(INPUT_ROOT.rglob("_output_.zip"))
    if not zips:
        raise SystemExit("stage-4 output not attached (no manifest_clean.csv or _output_.zip)")
    # extract to /tmp (NOT /kaggle/working) so it isn't re-saved as kernel
    # output — keeps the output zip small and the log downloadable on error
    extract_dir = Path("/tmp/stage4_data")
    extract_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extracting {zips[0]} ({zips[0].stat().st_size/1e9:.2f} GB) ...")
    with zipfile.ZipFile(zips[0]) as zf:
        zf.extractall(extract_dir)
    manifests = list(extract_dir.rglob("manifest_clean.csv"))
    if not manifests:
        raise SystemExit("_output_.zip extracted but no manifest_clean.csv inside")
MANIFEST = manifests[0]
SRC = MANIFEST.parent
print("Stage-4 root:", SRC)

rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))
labels_sorted = sorted({r["label"] for r in rows})
label_to_id = {l: i for i, l in enumerate(labels_sorted)}
NUM_CLASSES = len(labels_sorted)
print(f"{len(rows):,} rows, {NUM_CLASSES} classes")

(OUT / "exports" / "cpl_id_to_label.json").write_text(
    json.dumps({str(i): l for i, l in enumerate(labels_sorted)}, indent=2))
(OUT / "exports" / "cpl_preprocessing_config.json").write_text(json.dumps({
    "model_backbone": "efficientnetv2b2", "image_size": list(IMG), "batch_size": BATCH,
}, indent=2))

# %% [markdown]
# ## File lists

# %%
train_by_class: dict[int, list[str]] = {c: [] for c in range(NUM_CLASSES)}
val_clean_p, val_clean_y = [], []
val_field_p, val_field_y = [], []
test_clean_p, test_clean_y = [], []
test_field_p, test_field_y = [], []

for r in rows:
    y = label_to_id[r["label"]]
    clean = SRC / r["clean_relpath"]
    comp = SRC / r["composite_relpath"] if r.get("composite_relpath") else None
    if not clean.exists():
        continue
    if r["split"] == "train":
        train_by_class[y].append(str(clean))
        if comp is not None and comp.exists():
            train_by_class[y].append(str(comp))
    elif r["split"] == "val":
        val_clean_p.append(str(clean)); val_clean_y.append(y)
        if comp is not None and comp.exists():
            val_field_p.append(str(comp)); val_field_y.append(y)
    else:
        test_clean_p.append(str(clean)); test_clean_y.append(y)
        if comp is not None and comp.exists():
            test_field_p.append(str(comp)); test_field_y.append(y)

pool = sum(len(v) for v in train_by_class.values())
sizes = {c: len(v) for c, v in train_by_class.items()}
print(f"train pool={pool:,}  val: clean={len(val_clean_p):,} field={len(val_field_p):,}"
      f"  test: clean={len(test_clean_p):,} field={len(test_field_p):,}")

sq = {c: math.sqrt(n) for c, n in sizes.items() if n > 0}
ssum = sum(sq.values())
sample_p = [sq.get(c, 0.0) / ssum for c in range(NUM_CLASSES)]
print(f"sqrt-sampling: top class exposure {100*max(n/pool for n in sizes.values()):.1f}%"
      f" -> {100*max(sample_p):.1f}%")

# %% [markdown]
# ## tf.data — balanced sampling, internet-photo augmentation, mixup

# %%
AUTO = tf.data.AUTOTUNE

batch_augment = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal_and_vertical"),
    tf.keras.layers.RandomRotation(0.12),
    tf.keras.layers.RandomZoom(0.15),
    tf.keras.layers.RandomContrast(0.25),
    tf.keras.layers.RandomBrightness(0.25, value_range=(0.0, 255.0)),
    # NOTE: keras GaussianNoise requires stddev in [0,1] (normalized inputs);
    # ours are 0..255, so sensor noise is added in decode_train instead.
], name="field_augmentation")


def cutout(img: tf.Tensor) -> tf.Tensor:
    """Random black square (matches bg fill) — occlusion robustness."""
    h, w = IMG
    s = tf.random.uniform([], 26, 70, tf.int32)  # 10-27% of side
    cy = tf.random.uniform([], 0, h, tf.int32)
    cx = tf.random.uniform([], 0, w, tf.int32)
    y0, y1 = tf.maximum(0, cy - s // 2), tf.minimum(h, cy + s // 2)
    x0, x1 = tf.maximum(0, cx - s // 2), tf.minimum(w, cx + s // 2)
    mask = tf.pad(tf.zeros((y1 - y0, x1 - x0), img.dtype),
                  [[y0, h - y1], [x0, w - x1]], constant_values=1.0)
    return img * mask[..., None]


def decode_train(path: tf.Tensor, label: tf.Tensor):
    raw = tf.io.read_file(path)
    img = tf.io.decode_jpeg(raw, channels=3)  # uint8
    # internet-photo realism: random recompression + white-balance jitter
    img = tf.cond(tf.random.uniform([]) < 0.5,
                  lambda: tf.image.random_jpeg_quality(img, 40, 95), lambda: img)
    img = tf.image.random_hue(img, 0.05)
    img = tf.image.random_saturation(img, 0.7, 1.3)
    img = tf.image.resize(img, IMG, method="bilinear")
    img = tf.cast(img, tf.float32)
    img = tf.cond(tf.random.uniform([]) < 0.5, lambda: cutout(img), lambda: img)
    # sensor noise on the 0..255 scale (replaces keras GaussianNoise layer)
    img = img + tf.random.normal(tf.shape(img), stddev=6.0)
    img = tf.clip_by_value(img, 0.0, 255.0)
    return img, tf.one_hot(label, NUM_CLASSES)


def decode_eval(path: tf.Tensor, label: tf.Tensor):
    raw = tf.io.read_file(path)
    img = tf.io.decode_jpeg(raw, channels=3)
    img = tf.image.resize(img, IMG, method="bilinear")
    return tf.cast(img, tf.float32), tf.one_hot(label, NUM_CLASSES)


def mixup(x: tf.Tensor, y: tf.Tensor):
    """Mixup on 50% of batches; Beta(a,a) via two Gammas."""
    def _mix():
        g1 = tf.random.gamma([], MIXUP_ALPHA)
        g2 = tf.random.gamma([], MIXUP_ALPHA)
        lam = g1 / (g1 + g2)
        idx = tf.random.shuffle(tf.range(tf.shape(x)[0]))
        return (lam * x + (1.0 - lam) * tf.gather(x, idx),
                lam * y + (1.0 - lam) * tf.gather(y, idx))
    return tf.cond(tf.random.uniform([]) < MIXUP_PROB, _mix, lambda: (x, y))


def class_ds(c: int) -> tf.data.Dataset:
    paths = train_by_class[c]
    ds = tf.data.Dataset.from_tensor_slices(
        (tf.constant(paths), tf.constant([c] * len(paths), tf.int32)))
    return ds.shuffle(len(paths), seed=SEED, reshuffle_each_iteration=True).repeat()


train_ds = tf.data.Dataset.sample_from_datasets(
    [class_ds(c) for c in range(NUM_CLASSES) if sizes[c] > 0],
    weights=[p for c, p in enumerate(sample_p) if sizes[c] > 0], seed=SEED)
train_ds = (train_ds.map(decode_train, num_parallel_calls=AUTO)
            .batch(BATCH)
            # under mixed_float16 the keras augment stack emits float16 —
            # cast back so mixup's float32 arithmetic doesn't dtype-clash
            .map(lambda x, y: (tf.cast(batch_augment(x, training=True), tf.float32), y),
                 num_parallel_calls=AUTO)
            .map(mixup, num_parallel_calls=AUTO)
            .prefetch(AUTO))
STEPS = pool // BATCH


def eval_ds(paths, ys) -> tf.data.Dataset:
    ds = tf.data.Dataset.from_tensor_slices(
        (tf.constant(paths), tf.constant(ys, tf.int32)))
    return ds.map(decode_eval, num_parallel_calls=AUTO).batch(BATCH).prefetch(AUTO)


# checkpoint selection sees BOTH worlds: clean + field-proxy validation
val_ds = eval_ds(val_clean_p + val_field_p, val_clean_y + val_field_y)
test_clean_ds = eval_ds(test_clean_p, test_clean_y)
test_field_ds = eval_ds(test_field_p, test_field_y)

# %% [markdown]
# ## Model — EfficientNetV2-B2, two-phase (head -> full fine-tune, cosine LR)

# %%
def compile_model(m: tf.keras.Model, lr) -> None:
    m.compile(
        optimizer=tf.keras.optimizers.Adam(lr),
        loss=tf.keras.losses.CategoricalCrossentropy(
            from_logits=True, label_smoothing=SMOOTH),
        metrics=[
            tf.keras.metrics.CategoricalAccuracy(name="acc"),
            tf.keras.metrics.TopKCategoricalAccuracy(k=3, name="top3"),
            tf.keras.metrics.F1Score(average="macro", name="macro_f1"),
        ],
    )


base = tf.keras.applications.EfficientNetV2B2(
    include_top=False, weights="imagenet", input_shape=(*IMG, 3), pooling="avg")
base.trainable = False
inp = tf.keras.layers.Input(shape=(*IMG, 3))
x = base(inp, training=False)   # BN frozen for good — canonical fine-tune pattern
x = tf.keras.layers.Dropout(DROPOUT)(x)
logits = tf.keras.layers.Dense(NUM_CLASSES, dtype="float32", name="logits")(x)
model = tf.keras.Model(inp, logits)

ckpt = str(OUT / "models" / "best.weights.h5")


def callbacks(tag: str) -> list:
    return [
        tf.keras.callbacks.ModelCheckpoint(ckpt, monitor="val_macro_f1", mode="max",
                                           save_best_only=True, save_weights_only=True),
        tf.keras.callbacks.EarlyStopping(monitor="val_macro_f1", mode="max",
                                         patience=4, restore_best_weights=True),
        tf.keras.callbacks.CSVLogger(str(OUT / "reports" / f"history_{tag}.csv")),
    ]


print("\n--- Phase 1: head only ---")
compile_model(model, LR_HEAD)
model.fit(train_ds, validation_data=val_ds, epochs=HEAD_EPOCHS,
          steps_per_epoch=STEPS, callbacks=callbacks("head"), verbose=2)

print("\n--- Phase 2: FULL backbone fine-tune, cosine LR decay ---")
base.trainable = True
compile_model(model, tf.keras.optimizers.schedules.CosineDecay(
    LR_FT, decay_steps=FT_EPOCHS * STEPS, alpha=0.01))
model.fit(train_ds, validation_data=val_ds, epochs=FT_EPOCHS,
          steps_per_epoch=STEPS, callbacks=callbacks("ft"), verbose=2)
model.load_weights(ckpt)

# %% [markdown]
# ## Temperature calibration (combined val)

# %%
val_logits = model.predict(val_ds, verbose=0)
labels_t = tf.constant(np.array(val_clean_y + val_field_y, np.int64))
logits_t = tf.constant(val_logits, tf.float32)
log_T = tf.Variable(0.0, dtype=tf.float32)
opt = tf.keras.optimizers.Adam(0.05)
for _ in range(300):
    with tf.GradientTape() as tape:
        loss = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=labels_t, logits=logits_t / tf.exp(log_T)))
    opt.apply_gradients([(tape.gradient(loss, log_T), log_T)])
T = float(tf.exp(log_T).numpy())
print(f"Calibrated temperature T = {T:.3f}")
(OUT / "reports" / "calibration.json").write_text(json.dumps({"temperature": T}))

# %% [markdown]
# ## Export SavedModel (0..255 float in, calibrated probs out)

# %%
inp2 = tf.keras.layers.Input(shape=(*IMG, 3), name="image")
out = tf.keras.layers.Softmax(name="crop_disease_prediction", dtype="float32")(
    tf.keras.layers.Lambda(lambda z: z / T, dtype="float32")(model(inp2)))
serving = tf.keras.Model(inp2, out)
sm_dir = OUT / "exports" / "saved_model"
serving.export(str(sm_dir))  # Keras 3 export API (tf.saved_model.save fails on Keras 3 models)
print("SavedModel written:", sm_dir)

# verify the export round-trips before declaring success
_m = tf.saved_model.load(str(sm_dir))
_f = _m.signatures["serving_default"]
_p = list(_f(tf.constant(np.zeros((1, *IMG, 3), np.float32))).values())[0].numpy()
assert _p.shape[-1] == NUM_CLASSES and abs(_p.sum() - 1.0) < 1e-3
print("export verified: serving_default ->", _p.shape)

# %% [markdown]
# ## Test evaluation — CLEAN vs FIELD, micro + macro + per-crop

# %%
def evaluate(name: str, ds, ys) -> dict:
    probs = serving.predict(ds, verbose=0)
    y_true = np.array(ys)
    y_pred = probs.argmax(1)
    top3 = np.argsort(-probs, axis=1)[:, :3]
    top1 = float((y_pred == y_true).mean())
    top3a = float(np.mean([t in r for t, r in zip(y_true, top3)]))

    f1s, recalls, per_class = [], [], {}
    for c in range(NUM_CLASSES):
        tp = int(((y_pred == c) & (y_true == c)).sum())
        fp = int(((y_pred == c) & (y_true != c)).sum())
        fn = int(((y_pred != c) & (y_true == c)).sum())
        if tp + fn == 0:
            continue
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn)
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        f1s.append(f1); recalls.append(rec)
        per_class[labels_sorted[c]] = {"n": tp + fn, "recall": round(rec, 4),
                                       "f1": round(f1, 4)}
    crop_acc: dict[str, list[int]] = {}
    for t, p in zip(y_true, y_pred):
        crop = labels_sorted[t].split("::")[0]
        crop_acc.setdefault(crop, [0, 0])
        crop_acc[crop][0] += int(t == p)
        crop_acc[crop][1] += 1

    res = {"top1": top1, "top3": top3a, "macro_f1": float(np.mean(f1s)),
           "balanced_acc": float(np.mean(recalls)),
           "per_crop_acc": {c: v[0] / v[1] for c, v in crop_acc.items()},
           "per_class": per_class, "n": int(len(y_true))}
    print(f"\n[{name}] top1={top1:.4f} top3={top3a:.4f} "
          f"macroF1={res['macro_f1']:.4f} balanced={res['balanced_acc']:.4f}")
    print(f"  per-crop: " + "  ".join(
        f"{c}={v:.2f}" for c, v in sorted(res["per_crop_acc"].items())))
    return res


results = {
    "clean_test": evaluate("CLEAN test", test_clean_ds, test_clean_y),
    "field_test": evaluate("FIELD test", test_field_ds, test_field_y),
    "temperature": T,
    "num_classes": NUM_CLASSES,
}
(OUT / "reports" / "test_metrics.json").write_text(json.dumps(results, indent=2))

worst = sorted(results["field_test"]["per_class"].items(), key=lambda kv: kv[1]["f1"])[:10]
print("\nWorst 10 FIELD classes by F1:")
for nm, d in worst:
    print(f"  {nm:50s} f1={d['f1']:.2f} recall={d['recall']:.2f} (n={d['n']})")

print("\nStage 5 complete.")
