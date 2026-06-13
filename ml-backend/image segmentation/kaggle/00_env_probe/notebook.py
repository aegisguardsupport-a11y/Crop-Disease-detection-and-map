# %% [markdown]
# # CPL 00 — Kaggle environment probe + stage-5 miniature
#
# Runs the ENTIRE stage-5 computation graph in miniature on synthetic data
# (every op, layer, callback, the calibration loop and the SavedModel export)
# directly on Kaggle's environment. If this passes, stage 5 cannot fail on
# an API/version/dtype issue — only on data or resource limits.

# %%
import json
import platform
import sys

import numpy as np
import tensorflow as tf

print("python   :", sys.version)
print("platform :", platform.platform())
print("tf       :", tf.__version__)
print("keras    :", tf.keras.__version__)
print("numpy    :", np.__version__)
gpus = tf.config.list_physical_devices("GPU")
print("GPU      :", gpus)

tf.keras.mixed_precision.set_global_policy("mixed_float16")
print("policy   :", tf.keras.mixed_precision.global_policy())

IMG = (260, 260)
NUM = 4
BATCH = 4
MIXUP_ALPHA, MIXUP_PROB, SMOOTH = 0.2, 0.5, 0.1

# %% [markdown]
# ## Synthetic "corpus": real JPEG bytes so decode path is identical

# %%
import os
os.makedirs("/tmp/probe", exist_ok=True)
paths, labels = [], []
for i in range(16):
    img = tf.cast(tf.random.uniform((300, 300, 3), 0, 255), tf.uint8)
    p = f"/tmp/probe/{i}.jpg"
    tf.io.write_file(p, tf.io.encode_jpeg(img))
    paths.append(p)
    labels.append(i % NUM)
print("synthetic jpegs:", len(paths))

# %% [markdown]
# ## Exact stage-5 pipeline ops

# %%
AUTO = tf.data.AUTOTUNE

batch_augment = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal_and_vertical"),
    tf.keras.layers.RandomRotation(0.12),
    tf.keras.layers.RandomZoom(0.15),
    tf.keras.layers.RandomContrast(0.25),
    tf.keras.layers.RandomBrightness(0.25, value_range=(0.0, 255.0)),
], name="field_augmentation")


def cutout(img):
    h, w = IMG
    s = tf.random.uniform([], 26, 70, tf.int32)
    cy = tf.random.uniform([], 0, h, tf.int32)
    cx = tf.random.uniform([], 0, w, tf.int32)
    y0, y1 = tf.maximum(0, cy - s // 2), tf.minimum(h, cy + s // 2)
    x0, x1 = tf.maximum(0, cx - s // 2), tf.minimum(w, cx + s // 2)
    mask = tf.pad(tf.zeros((y1 - y0, x1 - x0), img.dtype),
                  [[y0, h - y1], [x0, w - x1]], constant_values=1.0)
    return img * mask[..., None]


def decode_train(path, label):
    raw = tf.io.read_file(path)
    img = tf.io.decode_jpeg(raw, channels=3)
    img = tf.cond(tf.random.uniform([]) < 0.5,
                  lambda: tf.image.random_jpeg_quality(img, 40, 95), lambda: img)
    img = tf.image.random_hue(img, 0.05)
    img = tf.image.random_saturation(img, 0.7, 1.3)
    img = tf.image.resize(img, IMG, method="bilinear")
    img = tf.cast(img, tf.float32)
    img = tf.cond(tf.random.uniform([]) < 0.5, lambda: cutout(img), lambda: img)
    img = img + tf.random.normal(tf.shape(img), stddev=6.0)
    img = tf.clip_by_value(img, 0.0, 255.0)
    return img, tf.one_hot(label, NUM)


def mixup(x, y):
    def _mix():
        g1 = tf.random.gamma([], MIXUP_ALPHA)
        g2 = tf.random.gamma([], MIXUP_ALPHA)
        lam = g1 / (g1 + g2)
        idx = tf.random.shuffle(tf.range(tf.shape(x)[0]))
        return (lam * x + (1.0 - lam) * tf.gather(x, idx),
                lam * y + (1.0 - lam) * tf.gather(y, idx))
    return tf.cond(tf.random.uniform([]) < MIXUP_PROB, _mix, lambda: (x, y))


def class_ds(c):
    ps = [p for p, l in zip(paths, labels) if l == c]
    ds = tf.data.Dataset.from_tensor_slices(
        (tf.constant(ps), tf.constant([c] * len(ps), tf.int32)))
    return ds.shuffle(len(ps)).repeat()


train_ds = tf.data.Dataset.sample_from_datasets(
    [class_ds(c) for c in range(NUM)], weights=[0.25] * NUM, seed=42)
train_ds = (train_ds.map(decode_train, num_parallel_calls=AUTO)
            .batch(BATCH)
            .map(lambda x, y: (tf.cast(batch_augment(x, training=True), tf.float32), y),
                 num_parallel_calls=AUTO)
            .map(mixup, num_parallel_calls=AUTO)
            .prefetch(AUTO))

val_ds = (tf.data.Dataset.from_tensor_slices(
    (tf.constant(paths), tf.constant(labels, tf.int32)))
    .map(lambda p, l: (tf.cast(tf.image.resize(
        tf.io.decode_jpeg(tf.io.read_file(p), channels=3), IMG), tf.float32),
        tf.one_hot(l, NUM)))
    .batch(BATCH).prefetch(AUTO))

for xb, yb in train_ds.take(2):
    pass
print("pipeline OK — batch dtypes:", xb.dtype, yb.dtype, "shapes:", xb.shape, yb.shape)

# %% [markdown]
# ## Model build (imagenet download), two-phase compile/fit, callbacks

# %%
def compile_model(m, lr):
    m.compile(
        optimizer=tf.keras.optimizers.Adam(lr),
        loss=tf.keras.losses.CategoricalCrossentropy(from_logits=True,
                                                     label_smoothing=SMOOTH),
        metrics=[tf.keras.metrics.CategoricalAccuracy(name="acc"),
                 tf.keras.metrics.TopKCategoricalAccuracy(k=3, name="top3"),
                 tf.keras.metrics.F1Score(average="macro", name="macro_f1")],
    )


base = tf.keras.applications.EfficientNetV2B2(
    include_top=False, weights="imagenet", input_shape=(*IMG, 3), pooling="avg")
base.trainable = False
inp = tf.keras.layers.Input(shape=(*IMG, 3))
x = base(inp, training=False)
x = tf.keras.layers.Dropout(0.35)(x)
logits = tf.keras.layers.Dense(NUM, dtype="float32", name="logits")(x)
model = tf.keras.Model(inp, logits)
print("model built, params:", model.count_params())

cbs = [
    tf.keras.callbacks.ModelCheckpoint("/tmp/best.weights.h5", monitor="val_macro_f1",
                                       mode="max", save_best_only=True,
                                       save_weights_only=True),
    tf.keras.callbacks.EarlyStopping(monitor="val_macro_f1", mode="max", patience=4,
                                     restore_best_weights=True),
    tf.keras.callbacks.CSVLogger("/tmp/hist.csv"),
]
compile_model(model, 1e-3)
model.fit(train_ds, validation_data=val_ds, epochs=2, steps_per_epoch=2,
          callbacks=cbs, verbose=2)
print("phase-1 fit OK")

base.trainable = True
compile_model(model, tf.keras.optimizers.schedules.CosineDecay(1e-4, decay_steps=8,
                                                               alpha=0.01))
model.fit(train_ds, validation_data=val_ds, epochs=2, steps_per_epoch=2,
          callbacks=cbs, verbose=2)
model.load_weights("/tmp/best.weights.h5")
print("phase-2 fit + checkpoint reload OK")

# %% [markdown]
# ## Calibration loop + SavedModel export + reload

# %%
val_logits = model.predict(val_ds, verbose=0)
labels_t = tf.constant(np.array(labels, np.int64))
logits_t = tf.constant(val_logits, tf.float32)
log_T = tf.Variable(0.0, dtype=tf.float32)
opt = tf.keras.optimizers.Adam(0.05)
for _ in range(20):
    with tf.GradientTape() as tape:
        loss = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=labels_t, logits=logits_t / tf.exp(log_T)))
    opt.apply_gradients([(tape.gradient(loss, log_T), log_T)])
T = float(tf.exp(log_T).numpy())
print(f"calibration OK, T={T:.3f}")

inp2 = tf.keras.layers.Input(shape=(*IMG, 3), name="image")
out = tf.keras.layers.Softmax(name="crop_disease_prediction", dtype="float32")(
    tf.keras.layers.Lambda(lambda z: z / T, dtype="float32")(model(inp2)))
serving = tf.keras.Model(inp2, out)
serving.export("/tmp/sm")  # Keras 3 export API (tf.saved_model.save fails on Keras 3 models)
m2 = tf.saved_model.load("/tmp/sm")
f = m2.signatures["serving_default"]
probs = list(f(tf.constant(np.zeros((1, *IMG, 3), np.float32))).values())[0].numpy()
assert probs.shape[-1] == NUM and abs(probs.sum() - 1.0) < 1e-3
print("export + reload + softmax inference OK")

print("\n############ PROBE: ALL PASSED ############")
