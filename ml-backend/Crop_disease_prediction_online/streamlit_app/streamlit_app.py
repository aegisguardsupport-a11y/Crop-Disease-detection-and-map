"""Streamlit demo UI for the CPL Crop Disease /predict-v2 endpoint.

Drop a leaf photo, see the entire validation pipeline render step by step:
quality -> YOLO segmentation -> clean leaf -> classification -> confidence
-> decision -> explanation. Every signal in the API response gets its
own panel.

Run with: ``streamlit run streamlit_app/streamlit_app.py``

The API URL defaults to ``http://127.0.0.1:8000`` but can be overridden
via the ``API_BASE_URL`` environment variable (used by docker-compose).
"""

from __future__ import annotations

import base64
import io
import os
from typing import Any

import httpx
import pandas as pd
import streamlit as st
from PIL import Image

DEFAULT_API_BASE = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CPL Crop Disease Diagnostics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject minimal CSS for a tighter look
st.markdown(
    """
    <style>
    .decision-banner {
        padding: 1.0rem 1.25rem;
        border-radius: 0.5rem;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
    .decision-high   { background: #d1f7e0; color: #1a6c3a; border: 1px solid #84d9a8; }
    .decision-medium { background: #fff5cc; color: #8a6d00; border: 1px solid #f0d77b; }
    .decision-low    { background: #fde2e2; color: #8a1a1a; border: 1px solid #f0a0a0; }
    .step-pass { color: #1a7c33; }
    .step-fail { color: #8a1a1a; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Settings")
    api_base = st.text_input(
        "API base URL",
        value=DEFAULT_API_BASE,
        help="Where the FastAPI service is running. Defaults to API_BASE_URL env var or http://127.0.0.1:8000.",
    )
    topk = st.slider("Top-K predictions", min_value=1, max_value=10, value=3)
    enable_explain = st.checkbox(
        "Generate SmoothGrad explanation",
        value=True,
        help="Adds ~1-2 s latency. Produces a saliency heatmap overlay.",
    )

    st.divider()
    st.subheader("Health")
    health_placeholder = st.empty()

    if st.button("Check server"):
        try:
            r = httpx.get(f"{api_base}/ready", timeout=5.0)
            if r.status_code == 200:
                body = r.json()
                health_placeholder.success(
                    f"✅ Ready — {body.get('num_classes', '?')} classes, "
                    f"model {body.get('model_version', '?')}"
                )
            else:
                health_placeholder.warning(f"Status {r.status_code}: {r.text[:200]}")
        except httpx.RequestError as e:
            health_placeholder.error(f"❌ {type(e).__name__}: {e}")

    st.divider()
    st.markdown(
        "**Pipeline stages**\n\n"
        "1. File validation\n"
        "2. Image quality (OpenCV)\n"
        "3. Leaf segmentation (YOLOv8-seg)\n"
        "4. Leaf-area validation\n"
        "5. Background removal\n"
        "6. Disease classification\n"
        "7. Confidence engine\n"
        "8. Decision router\n"
        "9. RAG advisory\n"
    )

# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------
st.title("🌿 CPL Crop Disease Diagnostics")
st.caption(
    "Upload a leaf photo. The system runs the full validation pipeline "
    "and shows every step's output."
)

uploaded = st.file_uploader(
    "Drop or click to upload a leaf image (JPEG / PNG, ≤10 MB)",
    type=["jpg", "jpeg", "png", "bmp", "webp"],
    accept_multiple_files=False,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def call_predict_v2(
    api_base: str, file_bytes: bytes, filename: str, mime: str, topk: int, explain: bool
) -> dict[str, Any]:
    url = f"{api_base.rstrip('/')}/predict-v2"
    params = {"topk": str(topk), "explain": "true" if explain else "false"}
    files = {"file": (filename, file_bytes, mime)}
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, params=params, files=files)
    resp.raise_for_status()
    return resp.json()


def decode_b64_to_image(b64: str | None) -> Image.Image | None:
    if not b64:
        return None
    return Image.open(io.BytesIO(base64.b64decode(b64)))


def decision_class(decision: str) -> str:
    return {
        "high_confidence": "decision-high",
        "expert_review": "decision-medium",
        "retake": "decision-low",
    }.get(decision, "decision-medium")


def decision_label(decision: str) -> str:
    return {
        "high_confidence": "✅ HIGH CONFIDENCE — auto-accept",
        "expert_review": "⚠️ EXPERT REVIEW — flag for human verification",
        "retake": "❌ RETAKE — image cannot be reliably diagnosed",
    }.get(decision, decision)


def step(label: str, ok: bool, detail: str = "") -> None:
    """Render one timeline step."""
    icon = "✅" if ok else "❌"
    cls = "step-pass" if ok else "step-fail"
    st.markdown(
        f"<span class='{cls}'>{icon} <strong>{label}</strong>"
        f"{' — ' + detail if detail else ''}</span>",
        unsafe_allow_html=True,
    )


def render_bullets(title: str, items: list[str]) -> None:
    if items:
        st.markdown(f"**{title}**")
        for item in items:
            st.markdown(f"- {item}")


def render_advisory(advisory: dict[str, Any] | None) -> None:
    st.subheader("Disease explanation & precautions")
    if not advisory:
        st.info(
            "RAG advisory is not available yet. Build rag/chroma_db and set "
            "GEMINI_API_KEY on the API server to enable final explanations."
        )
        return

    status = advisory.get("status", "unknown")
    if status == "ok":
        st.success(advisory.get("summary", "Advisory generated."))
    elif status == "retake":
        st.warning(advisory.get("summary", "Please retake the image."))
    else:
        st.warning(advisory.get("summary", "Advisory generated with limited context."))

    render_bullets("Symptoms to check", advisory.get("symptoms_to_check", []))
    render_bullets("Immediate actions", advisory.get("immediate_actions", []))
    render_bullets("Precautions", advisory.get("precautions", []))
    render_bullets("Prevention", advisory.get("prevention", []))
    render_bullets("Similar diseases or issues", advisory.get("similar_diseases", []))

    if advisory.get("expert_advice"):
        st.markdown(f"**Expert advice:** {advisory['expert_advice']}")
    if advisory.get("safety_note"):
        st.caption(advisory["safety_note"])

    citations = advisory.get("retrieved_chunks", [])
    if citations:
        with st.expander("Retrieved RAG chunks", expanded=False):
            st.dataframe(pd.DataFrame(citations), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------
if uploaded is None:
    st.info("Upload a leaf image to start. Try a tomato/potato/grape leaf first.")
    st.stop()

uploaded_bytes = uploaded.read()
original_image = Image.open(io.BytesIO(uploaded_bytes))

with st.spinner(f"Calling {api_base}/predict-v2 …"):
    try:
        body = call_predict_v2(
            api_base=api_base,
            file_bytes=uploaded_bytes,
            filename=uploaded.name,
            mime=uploaded.type or "image/jpeg",
            topk=topk,
            explain=enable_explain,
        )
    except httpx.HTTPStatusError as e:
        st.error(f"Server returned {e.response.status_code}")
        st.code(e.response.text[:500] or "<empty body>")
        st.stop()
    except httpx.RequestError as e:
        st.error(f"Could not reach the server at {api_base}: {e}")
        st.stop()

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
decision = body.get("decision", "?")
confidence = float(body.get("confidence", 0.0))

# Decision banner
banner_text = decision_label(decision)
st.markdown(
    f"<div class='decision-banner {decision_class(decision)}'>"
    f"{banner_text}<br>"
    f"<span style='font-size: 1.0rem; opacity: 0.85;'>"
    f"final confidence: {confidence * 100:.1f}%</span>"
    f"</div>",
    unsafe_allow_html=True,
)

# Retake guidance prominently if applicable
if decision == "retake" and body.get("retake_guidance"):
    st.warning(f"💡 {body['retake_guidance']}")

render_advisory(body.get("advisory"))

# Two-column layout
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.subheader("Original image")
    st.image(original_image, width=420)

    st.subheader("What the classifier saw")
    clean_leaf = decode_b64_to_image(body.get("clean_leaf_png_b64"))
    if clean_leaf is not None:
        st.image(clean_leaf, caption="Background-removed leaf, 260×260", width=320)
    else:
        st.caption("Not available — pipeline aborted before background removal.")

with right_col:
    # Predictions bar chart
    st.subheader("Disease predictions")
    preds = body.get("predictions", [])
    if preds:
        df = pd.DataFrame(
            [
                {
                    "label": f"{p['crop']} — {p['disease']}",
                    "confidence": float(p["confidence"]),
                }
                for p in preds
            ]
        )
        st.dataframe(
            df.assign(confidence=df["confidence"].apply(lambda v: f"{v * 100:.1f}%")),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(df.set_index("label"), height=240)
    else:
        st.info("No predictions returned (pipeline aborted before classification).")

    # Crop router (trained) — preferred when /predict-v2 used the hierarchical bundle.
    router_preds = body.get("crop_router_predictions", [])
    if router_preds:
        st.subheader("Crop router (trained)")
        st.caption(
            "P(crop) from the dedicated crop-router head — independent of the joint "
            "disease softmax, so it isn't biased by per-crop class counts."
        )
        rdf = pd.DataFrame(
            [{"crop": c["crop"], "P(crop)": float(c["confidence"])} for c in router_preds]
        )
        st.dataframe(
            rdf.assign(**{"P(crop)": rdf["P(crop)"].apply(lambda v: f"{v * 100:.1f}%")}),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(rdf.set_index("crop"), height=200)

    # Per-crop disease head — top diseases inside the router's top-1 crop.
    within_top = body.get("disease_within_top_crop", [])
    if within_top:
        top_crop_name = within_top[0]["crop"]
        st.subheader(f"Diseases within {top_crop_name} (per-crop head)")
        st.caption(
            f"Specialised classifier for {top_crop_name} only. Each crop in the bundle has "
            "its own LR head trained on that crop's diseases — typically 4–13 classes."
        )
        wdf = pd.DataFrame(
            [
                {"label": w["label"], "P(disease | crop)": float(w["confidence"])}
                for w in within_top
            ]
        )
        st.dataframe(
            wdf.assign(
                **{
                    "P(disease | crop)": wdf["P(disease | crop)"].apply(
                        lambda v: f"{v * 100:.1f}%"
                    )
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(wdf.set_index("label"), height=200)

    # Legacy marginalised crop ranking (only shown if hierarchical wasn't used).
    top_crops = body.get("top_crops", [])
    if top_crops and not router_preds:
        st.subheader("Crop confidence (marginalised — fallback)")
        st.caption(
            "P(crop) summed across that crop's diseases from the legacy 139-class "
            "EfficientNetB2 classifier. Used when the hierarchical bundle is unavailable."
        )
        crop_df = pd.DataFrame(
            [
                {
                    "crop": c["crop"],
                    "P(crop)": float(c["confidence"]),
                    "best disease (given crop)": c["top_disease"],
                    "P(disease | crop)": float(c["top_disease_conditional"]),
                }
                for c in top_crops
            ]
        )
        st.dataframe(
            crop_df.assign(
                **{
                    "P(crop)": crop_df["P(crop)"].apply(lambda v: f"{v * 100:.1f}%"),
                    "P(disease | crop)": crop_df["P(disease | crop)"].apply(lambda v: f"{v * 100:.1f}%"),
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(
            crop_df[["crop", "P(crop)"]].set_index("crop"),
            height=200,
        )

    # CLIP zero-shot crop verifier — independent second opinion
    cv_preds = body.get("crop_verifier_predictions", [])
    if cv_preds:
        st.subheader("🔍 Crop verifier — CLIP zero-shot")
        agreement = body.get("crop_verifier_agreement")
        if agreement is True:
            st.success("✓ CLIP top-1 crop matches classifier — agreement")
        elif agreement is False:
            st.warning(
                "⚠ CLIP and classifier disagree on the crop. "
                "Treat the disease prediction with caution; consider expert review."
            )
        st.caption(
            "Independent vote from OpenAI's CLIP foundation model. Compares "
            "the leaf image against text prompts like 'a photograph of a "
            "tomato leaf' for each of the bundle's 20 crops."
        )
        cv_df = pd.DataFrame(
            [
                {"crop": c["crop"], "CLIP similarity": float(c["similarity"])}
                for c in cv_preds
            ]
        )
        st.dataframe(
            cv_df.assign(
                **{"CLIP similarity": cv_df["CLIP similarity"].apply(lambda v: f"{v * 100:.1f}%")}
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(cv_df.set_index("crop"), height=200)

    # Explanation overlay
    overlay = decode_b64_to_image(body.get("explanation_overlay_png_b64"))
    if overlay is not None:
        st.subheader("Explanation (SmoothGrad)")
        st.image(overlay, caption="Red regions = pixels the model attended to", width=420)

# ---------------------------------------------------------------------------
# Step-by-step timeline
# ---------------------------------------------------------------------------
st.divider()
st.header("📋 Step-by-step pipeline trace")

with st.expander("Step 1 — Image quality (OpenCV)", expanded=True):
    q = body["validation"]["image_quality"]
    step(
        "Image quality",
        q["ok"],
        f"score {q['score']:.2f}, blur {q['blur']:.0f}, "
        f"brightness {q['brightness']:.0f}, contrast {q['contrast']:.0f}, "
        f"resolution {q['resolution'][0]}×{q['resolution'][1]}",
    )
    if q["failures"]:
        st.warning("Failures: " + ", ".join(q["failures"]))
    cols = st.columns(4)
    cols[0].metric("Quality score", f"{q['score']:.2f}")
    cols[1].metric("Blur", f"{q['blur']:.0f}")
    cols[2].metric("Brightness", f"{q['brightness']:.0f}")
    cols[3].metric("Contrast", f"{q['contrast']:.0f}")

with st.expander("Step 2 — Leaf segmentation (YOLOv8-seg)", expanded=True):
    s = body["validation"]["leaf_segmentation"]
    step(
        "Leaf detection",
        s["detected"],
        f"confidence {s['confidence']:.2f}, "
        f"{s['num_detections']} detection(s), "
        f"covers {s['leaf_area_ratio'] * 100:.1f}% of frame",
    )
    cols = st.columns(3)
    cols[0].metric("Seg confidence", f"{s['confidence']:.2f}")
    cols[1].metric("Detections", s["num_detections"])
    cols[2].metric("Leaf area", f"{s['leaf_area_ratio'] * 100:.1f}%")

    mask_overlay = decode_b64_to_image(body.get("mask_overlay_png_b64"))
    if mask_overlay is not None:
        st.image(mask_overlay, caption="Original image + YOLO mask (red overlay)", width=380)

with st.expander("Step 3 — Leaf area validation", expanded=False):
    la = body["validation"].get("leaf_area")
    if la:
        step(
            "Leaf area",
            la["ok"],
            f"score {la['score']:.2f}, ratio {la['ratio'] * 100:.1f}%"
            + (f", failure: {la['failure']}" if la.get("failure") else ""),
        )
    else:
        st.caption("Not run — segmentation didn't detect a leaf.")

with st.expander("Step 4 — Confidence engine", expanded=True):
    cs = body["confidence_signals"]
    df = pd.DataFrame(
        [
            {"signal": "quality", "value": cs["quality_score"], "weight": cs["weights"]["quality"]},
            {"signal": "segmentation", "value": cs["seg_confidence"], "weight": cs["weights"]["seg"]},
            {"signal": "leaf area", "value": cs["leaf_area_score"], "weight": cs["weights"]["area"]},
            {"signal": "classifier top-1", "value": cs["classifier_top1"], "weight": cs["weights"]["top1"]},
            {"signal": "prediction gap", "value": cs["prediction_gap"], "weight": cs["weights"]["gap"]},
        ]
    )
    df["contribution"] = (df["value"] * df["weight"]).round(4)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        f"final confidence = sum(value × weight) = **{cs['final']:.4f}**"
    )

with st.expander("Step 5 — Decision router", expanded=True):
    cls = decision_class(decision)
    st.markdown(
        f"<div class='decision-banner {cls}' style='margin-bottom:0;'>"
        f"{decision_label(decision)}</div>",
        unsafe_allow_html=True,
    )
    if body.get("retake_reason"):
        st.write(f"**Reason code:** `{body['retake_reason']}`")
    if body.get("retake_guidance"):
        st.write(f"**Guidance:** {body['retake_guidance']}")

# ---------------------------------------------------------------------------
# Latency breakdown + raw JSON
# ---------------------------------------------------------------------------
st.divider()
left, right = st.columns(2)
with left:
    st.subheader("⏱ Latency breakdown")
    lat = body.get("latency", {})
    lat_df = pd.DataFrame(
        [
            {"stage": "quality (OpenCV)", "ms": lat.get("quality_ms", 0)},
            {"stage": "segmentation (YOLO)", "ms": lat.get("segmentation_ms", 0)},
            {"stage": "extract clean leaf", "ms": lat.get("extract_ms", 0)},
            {"stage": "classification (EfficientNet)", "ms": lat.get("classification_ms", 0)},
            {"stage": "explanation (SmoothGrad)", "ms": lat.get("explain_ms", 0)},
            {"stage": "RAG advisory (Gemini)", "ms": lat.get("advisory_ms", 0)},
        ]
    )
    lat_df["ms"] = lat_df["ms"].round(1)
    st.dataframe(lat_df, use_container_width=True, hide_index=True)
    st.metric("Total", f"{lat.get('total_ms', 0):.0f} ms")

with right:
    st.subheader("🧾 Model versions")
    mv = body.get("model_versions", {})
    st.write(
        f"- **Leaf segmenter:** `{mv.get('leaf_segmenter', '?')}`\n"
        f"- **Disease classifier:** `{mv.get('disease_classifier', '?')}`\n"
        f"- **Request id:** `{body.get('request_id', '?')}`"
    )

with st.expander("🔧 Raw API response (debug)", expanded=False):
    # Hide the giant base64 PNGs in this view to keep it readable
    redacted = {
        k: ("<base64 PNG, omitted>" if k.endswith("_png_b64") and v else v)
        for k, v in body.items()
    }
    st.json(redacted)
