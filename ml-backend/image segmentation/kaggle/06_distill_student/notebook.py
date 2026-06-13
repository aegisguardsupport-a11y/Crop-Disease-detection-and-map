# %% [markdown]
# # CPL Crop Disease — Stage 6: Knowledge Distillation (offline student model)
#
# Distills the new EfficientNetV2-B2 teacher (72 classes, 97.7% clean / 89.9%
# field) into a tiny **MobileNetV3-Small** student for on-device / offline use.
#
# Inputs (kernel_sources):
# - `cpl-04-segment-preprocess` — the data: clean cutouts + field composites
#   (so the student learns the SAME field-robustness, not lab-only)
# - `cpl-05-train-classifier`   — the teacher's `best.weights.h5` + labels
#
# Outputs (for the offline kit):
# - `exports/cpl_student_int8.tflite`    — full int8, ~2-4 MB (the app loads this)
# - `exports/cpl_student_float.tflite`   — dynamic-range fallback
# - `exports/cpl_id_to_label.json`       — class index -> "crop::disease"
# - `exports/student_preprocessing.json` — input contract for the app
# - `reports/distill_metrics.json`       — teacher-vs-student, clean & field

# %%
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import tensorflow as tf

SEED = 42
tf.random.set_seed(SEED); np.random.seed(SEED)

INPUT_ROOT = Path("/kaggle/input")
OUT = Path("/kaggle/working")
(OUT / "exports").mkdir(parents=True, exist_ok=True)
(OUT / "reports").mkdir(parents=True, exist_ok=True)
(OUT / "models").mkdir(parents=True, exist_ok=True)

TEACHER_SIZE = (260, 260)
STUDENT_SIZE = (224, 224)
BATCH = 32
PHASE1_EPOCHS = 12      # student head only
PHASE1_LR = 1e-3
PHASE2_EPOCHS = 6       # + unfreeze last layers
PHASE2_LR = 1e-5
PHASE2_UNFREEZE = 40
KD_ALPHA = 0.5          # hard-loss vs soft-loss weight
KD_T = 4.0              # distillation temperature

print("TF", tf.__version__, "| GPUs:", tf.config.list_physical_devices("GPU"))

# %% [markdown]
# ## Locate inputs (data zip + teacher weights + labels)

# %%
manifests = list(INPUT_ROOT.rglob("manifest_clean.csv"))
if not manifests:
    zips = list(INPUT_ROOT.rglob("_output_.zip"))
    src_zip = next((z for z in zips if "segment" in str(z)), zips[0] if zips else None)
    if src_zip is None:
        raise SystemExit("stage-4 data not attached")
    extract = OUT / "stage4_data"; extract.mkdir(exist_ok=True)
    print(f"extracting {src_zip} ({src_zip.stat().st_size/1e9:.2f} GB) ...")
    with zipfile.ZipFile(src_zip) as zf:
        zf.extractall(extract)
    manifests = list(extract.rglob("manifest_clean.csv"))
MANIFEST = manifests[0]; SRC = MANIFEST.parent
print("data root:", SRC)

teacher_w = next(INPUT_ROOT.rglob("best.weights.h5"), None)
labels_json = next(INPUT_ROOT.rglob("cpl_id_to_label.json"), None)
if teacher_w is None or labels_json is None:
    raise SystemExit(f"teacher assets missing (weights={teacher_w}, labels={labels_json})")
print("teacher weights:", teacher_w)

labels = json.loads(labels_json.read_text())
labels_sorted = [labels[str(i)] for i in range(len(labels))]
NUM_CLASSES = len(labels_sorted)
label_to_id = {l: i for i, l in enumerate(labels_sorted)}
print("classes:", NUM_CLASSES)
(OUT / "exports" / "cpl_id_to_label.json").write_text(json.dumps(labels, indent=2))

import csv
rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))

# %% [markdown]
# ## Rebuild the teacher (EfficientNetV2-B2 + head) and load its weights

# %%
def build_teacher() -> tf.keras.Model:
    base = tf.keras.applications.EfficientNetV2B2(
        include_top=False, weights="imagenet", input_shape=(*TEACHER_SIZE, 3), pooling="avg")
    base.trainable = False
    inp = tf.keras.layers.Input(shape=(*TEACHER_SIZE, 3))
    x = base(inp, training=False)
    x = tf.keras.layers.Dropout(0.35)(x)
    logits = tf.keras.layers.Dense(NUM_CLASSES, dtype="float32", name="logits")(x)
    return tf.keras.Model(inp, logits)

teacher = build_teacher()
teacher.load_weights(str(teacher_w))
teacher.trainable = False
print("teacher rebuilt + weights loaded, params:", teacher.count_params())

# sanity: teacher should predict confidently on a clean image
_p = list(SRC.rglob("clean/*/*/*.jpg"))[:1]
if _p:
    _im = tf.image.resize(tf.io.decode_jpeg(tf.io.read_file(str(_p[0])), channels=3), TEACHER_SIZE)
    _pr = tf.nn.softmax(teacher(tf.cast(_im[None], tf.float32), training=False))[0].numpy()
    print(f"  teacher sanity: top prob {_pr.max():.3f} -> {labels_sorted[int(_pr.argmax())]}")

# %% [markdown]
# ## Data pipeline — one image, two resolutions (teacher 260, student 224)

# %%
def gather(split, with_composite):
    paths, ys = [], []
    for r in rows:
        if r["split"] != split:
            continue
        y = label_to_id[r["label"]]
        c = SRC / r["clean_relpath"]
        if c.exists():
            paths.append(str(c)); ys.append(y)
        if with_composite and r.get("composite_relpath"):
            cp = SRC / r["composite_relpath"]
            if cp.exists():
                paths.append(str(cp)); ys.append(y)
    return paths, ys

train_p, train_y = gather("train", True)
val_p, val_y = gather("val", False)
test_clean_p, test_clean_y = gather("test", False)
test_field_p, test_field_y = [], []
for r in rows:
    if r["split"] == "test" and r.get("composite_relpath"):
        cp = SRC / r["composite_relpath"]
        if cp.exists():
            test_field_p.append(str(cp)); test_field_y.append(label_to_id[r["label"]])
print(f"train={len(train_p):,}  val={len(val_p):,}  test_clean={len(test_clean_p):,}  test_field={len(test_field_p):,}")

AUTO = tf.data.AUTOTUNE
aug = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal_and_vertical"),
    tf.keras.layers.RandomRotation(0.10),
    tf.keras.layers.RandomZoom(0.12),
    tf.keras.layers.RandomContrast(0.15),
], name="aug")

def load_pair(path, label, training):
    raw = tf.io.read_file(path)
    img = tf.cast(tf.io.decode_jpeg(raw, channels=3), tf.float32)
    s = tf.image.resize(img, STUDENT_SIZE)
    t = tf.image.resize(img, TEACHER_SIZE)
    return (s, t), label

def make_ds(paths, ys, training):
    ds = tf.data.Dataset.from_tensor_slices((tf.constant(paths), tf.constant(ys, tf.int32)))
    if training:
        ds = ds.shuffle(min(len(paths), 20000), seed=SEED, reshuffle_each_iteration=True)
    ds = ds.map(lambda p, y: load_pair(p, y, training), num_parallel_calls=AUTO).batch(BATCH)
    if training:
        ds = ds.map(lambda xs, y: ((aug(xs[0], training=True), xs[1]), y), num_parallel_calls=AUTO)
    return ds.prefetch(AUTO)

train_ds = make_ds(train_p, train_y, True)
val_ds = make_ds(val_p, val_y, False)

# %% [markdown]
# ## Student (MobileNetV3-Small) + distillation loop

# %%
def build_student():
    base = tf.keras.applications.MobileNetV3Small(
        include_top=False, weights="imagenet",
        input_shape=(*STUDENT_SIZE, 3), include_preprocessing=True)
    base.trainable = False
    inp = tf.keras.layers.Input(shape=(*STUDENT_SIZE, 3), name="image")
    x = base(inp, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    logits = tf.keras.layers.Dense(NUM_CLASSES, name="student_logits")(x)
    return tf.keras.Model(inp, logits, name="student")

student = build_student()
print("student params:", student.count_params())


class Distiller(tf.keras.Model):
    def __init__(self, student, teacher, alpha, T):
        super().__init__()
        self.student, self.teacher = student, teacher
        self.alpha, self.T = alpha, T

    def compile(self, optimizer, hard_loss_fn):
        super().compile(optimizer=optimizer)
        self.hard_loss_fn = hard_loss_fn
        self.acc = tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")
        self.top3 = tf.keras.metrics.SparseTopKCategoricalAccuracy(k=3, name="top3")

    @property
    def metrics(self):
        return [self.acc, self.top3]

    def train_step(self, data):
        (sx, tx), y = data
        t_logits = self.teacher(tx, training=False)
        with tf.GradientTape() as tape:
            s_logits = self.student(sx, training=True)
            hard = self.hard_loss_fn(y, s_logits)
            soft = tf.keras.losses.KLDivergence()(
                tf.nn.softmax(t_logits / self.T, -1),
                tf.nn.softmax(s_logits / self.T, -1)) * (self.T ** 2)
            loss = self.alpha * hard + (1 - self.alpha) * soft
        g = tape.gradient(loss, self.student.trainable_variables)
        self.optimizer.apply_gradients(zip(g, self.student.trainable_variables))
        self.acc.update_state(y, s_logits); self.top3.update_state(y, s_logits)
        return {"loss": loss, "accuracy": self.acc.result(), "top3": self.top3.result()}

    def test_step(self, data):
        (sx, tx), y = data
        s_logits = self.student(sx, training=False)
        self.acc.update_state(y, s_logits); self.top3.update_state(y, s_logits)
        return {"accuracy": self.acc.result(), "top3": self.top3.result()}


distiller = Distiller(student, teacher, KD_ALPHA, KD_T)

print("\n--- Phase 1: student head ---")
distiller.compile(tf.keras.optimizers.Adam(PHASE1_LR),
                  tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True))
distiller.fit(train_ds, validation_data=val_ds, epochs=PHASE1_EPOCHS, verbose=2)

print("\n--- Phase 2: unfreeze last layers ---")
backbone = student.get_layer(index=1)
backbone.trainable = True
for i, layer in enumerate(backbone.layers):
    if i < len(backbone.layers) - PHASE2_UNFREEZE or isinstance(layer, tf.keras.layers.BatchNormalization):
        layer.trainable = False
distiller.compile(tf.keras.optimizers.Adam(PHASE2_LR),
                  tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True))
distiller.fit(train_ds, validation_data=val_ds, epochs=PHASE2_EPOCHS, verbose=2)

student.save_weights(str(OUT / "models" / "student.weights.h5"))

# %% [markdown]
# ## Evaluate student: clean vs field (vs teacher's numbers)

# %%
def evaluate(paths, ys):
    inf = tf.keras.Sequential([student, tf.keras.layers.Softmax()])
    correct = top3 = 0
    for i in range(0, len(paths), BATCH):
        bp = paths[i:i+BATCH]
        imgs = tf.stack([tf.image.resize(tf.cast(tf.io.decode_jpeg(tf.io.read_file(p), channels=3), tf.float32), STUDENT_SIZE) for p in bp])
        pr = inf(imgs, training=False).numpy()
        by = np.array(ys[i:i+BATCH])
        correct += int((pr.argmax(1) == by).sum())
        t3 = np.argsort(-pr, 1)[:, :3]
        top3 += int(sum(y in r for y, r in zip(by, t3)))
    return correct/len(paths), top3/len(paths)

c1, c3 = evaluate(test_clean_p, test_clean_y)
f1, f3 = evaluate(test_field_p, test_field_y)
print(f"STUDENT  clean top1={c1:.4f} top3={c3:.4f} | field top1={f1:.4f} top3={f3:.4f}")

# %% [markdown]
# ## Export TFLite (the app loads the int8 one)

# %%
inf_model = tf.keras.Sequential([
    tf.keras.layers.Input((*STUDENT_SIZE, 3)), student, tf.keras.layers.Softmax(name="probs")])
sm = OUT / "models" / "_student_sm"
inf_model.export(str(sm))   # Keras 3 export API

conv = tf.lite.TFLiteConverter.from_saved_model(str(sm))
conv.optimizations = [tf.lite.Optimize.DEFAULT]
(OUT / "exports" / "cpl_student_float.tflite").write_bytes(conv.convert())

# full int8 with calibration
def rep_data():
    sample = train_p[:200]
    for p in sample:
        im = tf.image.resize(tf.cast(tf.io.decode_jpeg(tf.io.read_file(p), channels=3), tf.float32), STUDENT_SIZE)
        yield [im[None].numpy()]
conv2 = tf.lite.TFLiteConverter.from_saved_model(str(sm))
conv2.optimizations = [tf.lite.Optimize.DEFAULT]
conv2.representative_dataset = rep_data
conv2.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
(OUT / "exports" / "cpl_student_int8.tflite").write_bytes(conv2.convert())

fsz = (OUT/"exports"/"cpl_student_float.tflite").stat().st_size/1e6
isz = (OUT/"exports"/"cpl_student_int8.tflite").stat().st_size/1e6
print(f"TFLite: float={fsz:.2f}MB  int8={isz:.2f}MB")

(OUT / "exports" / "student_preprocessing.json").write_text(json.dumps({
    "input_size": list(STUDENT_SIZE), "channels": 3, "pixel_range": "0..255 float32",
    "color": "RGB", "output": "softmax probabilities", "num_classes": NUM_CLASSES,
    "note": "MobileNetV3 normalizes internally; feed raw 0..255 RGB floats.",
}, indent=2))

(OUT / "reports" / "distill_metrics.json").write_text(json.dumps({
    "student_clean_top1": c1, "student_clean_top3": c3,
    "student_field_top1": f1, "student_field_top3": f3,
    "teacher_clean_top1": 0.9773, "teacher_field_top1": 0.8988,
    "student_params": int(student.count_params()),
    "tflite_int8_mb": isz, "num_classes": NUM_CLASSES,
    "kd_alpha": KD_ALPHA, "kd_temperature": KD_T,
}, indent=2))

# don't ship the extracted training data as kernel output
import shutil
shutil.rmtree(OUT / "stage4_data", ignore_errors=True)
print("Stage 6 (distillation) complete.")
