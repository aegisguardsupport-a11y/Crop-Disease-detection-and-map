# Crop Disease RAG

This folder holds generated RAG artifacts for the final `/predict-v2` advisory.

## Files

- `label_aliases.json` maps every model `crop::disease` label to the uploaded RAG record used for retrieval.
- `audit_report.json` summarizes direct, fuzzy, healthy, and fallback coverage.
- `chroma_db/` is generated after running the embedding/index build. Ship this folder with the API on Hugging Face.

## Build The Index

Run from `Crop_disease_prediction_online`:

```powershell
python scripts/build_rag_index.py --rag-dir ..\RAG
```

The script:

1. Parses all crop files in `..\RAG`.
2. Audits them against `exports/cpl_id_to_label.json`.
3. Creates disease-aware chunks with exact model-label metadata.
4. Embeds chunks using Chroma's free local default embedding function.
5. Stores them in `rag/chroma_db` with Chroma.

## Runtime

At API startup, RAG advisories are enabled only when both are present:

- `rag/chroma_db`
- `GEMINI_API_KEY` or `CPL_GEMINI_API_KEY`

The Gemini key is used only during runtime answer generation after local
retrieval. It is not used to build embeddings. For Hugging Face Spaces, add the
key as a Space secret named `GEMINI_API_KEY`.
