import json
import os
import glob

def check_missing_labels():
    try:
        with open('cpl_offline_kit/models/labels.json', 'r') as f:
            model_labels = json.load(f)
    except Exception as e:
        print(f"Error loading labels.json: {e}")
        return

    rag_labels = set()
    for f_path in glob.glob('RAG/*.txt'):
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    continue
                # Fixing common JSON trailing comma issues before loading
                import re
                content = re.sub(r',\s*\}', '}', content)
                content = re.sub(r',\s*\]', ']', content)
                data = json.loads(content)
                for obj in data:
                    model_support = obj.get('model_support', {})
                    labels = model_support.get('classification_labels', [])
                    for lbl in labels:
                        rag_labels.add(lbl)
        except Exception as e:
            print(f"Error parsing {f_path}: {e}")

    missing = []
    for label in model_labels:
        # Check if the exact label is in rag_labels
        if label not in rag_labels:
            # Maybe the label name was slightly altered in the RAG entry
            # E.g., 'Tomato___Two-spotted_spider_mite' might be mapped differently, but we used the exact names earlier?
            # Actually, the model labels in labels.json are like "Tomato___Bacterial_spot"
            # But the RAG classification_labels are just the string.
            # Wait, our RAG IDs used strings like "cabbage_bacterial_spot_rot".
            # Did the classification_labels array contain the EXACT strings from labels.json?
            missing.append(label)

    print("Model Labels:", len(model_labels))
    print("RAG Labels mapped:", len(rag_labels))
    
    # Actually, we need to check if the exact string or at least a close match exists
    # Let's print all missing labels
    if not missing:
        print("All labels are present.")
    else:
        print(f"Missing labels ({len(missing)}):")
        for m in missing:
            print(f" - {m}")
            
check_missing_labels()
