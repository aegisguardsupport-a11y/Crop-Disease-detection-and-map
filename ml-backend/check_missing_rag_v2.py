import json
import os
import glob
import re

def check_missing_labels():
    try:
        with open('cpl_offline_kit/models/labels.json', 'r') as f:
            model_labels_dict = json.load(f)
            # labels.json might be a dict {"0": "Crop___Disease"} or a list
            if isinstance(model_labels_dict, dict):
                model_labels = list(model_labels_dict.values())
            else:
                model_labels = model_labels_dict
    except Exception as e:
        print(f"Error loading labels.json: {e}")
        return

    # In my previous scripts, I inserted things like:
    # "classification_labels": ["cabbage_bacterial_spot_rot"]
    # But the model labels look like "Cabbage___Bacterial_spot_rot".
    # Since I didn't perfectly match the EXACT strings from labels.json (because I didn't have the exact strings in mind when making the new dicts, I just used the disease names), let's compare by normalizing the strings.

    def normalize(s):
        # convert to lowercase, replace non-alphanumeric with spaces
        s = s.lower().replace('___', ' ')
        s = re.sub(r'[^a-z0-string]', ' ', s)
        # return a set of words
        return set(s.split())

    rag_disease_names = []
    rag_ids = []

    for f_path in glob.glob('RAG/*.txt'):
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    continue
                content = re.sub(r',\s*\}', '}', content)
                content = re.sub(r',\s*\]', ']', content)
                data = json.loads(content)
                for obj in data:
                    crop = obj.get('crop', {}).get('common_name', '')
                    disease = obj.get('disease', {}).get('name', '')
                    rag_disease_names.append((crop, disease))
                    rag_ids.append(obj.get('id', ''))
        except Exception as e:
            print(f"Error parsing {f_path}: {e}")

    missing = []
    for label in model_labels:
        # A simple heuristic: check if the crop name and disease name appear in the RAG data
        # 'Cabbage___Bacterial_spot_rot' -> 'Cabbage', 'Bacterial_spot_rot'
        parts = label.split('___')
        if len(parts) == 2:
            l_crop = parts[0].lower().strip()
            l_disease = parts[1].lower().replace('_', ' ').strip()
            
            # Special case for "healthy"
            if 'healthy' in l_disease:
                continue

            found = False
            for rcrop, rdisease in rag_disease_names:
                rcrop = rcrop.lower().strip()
                rdisease = rdisease.lower().strip()
                if l_crop in rcrop or rcrop in l_crop:
                    # check if disease matches
                    if all(word in rdisease for word in l_disease.split() if word not in ['spot', 'rot', 'blight', 'leaf']) or all(word in l_disease for word in rdisease.split() if word not in ['spot', 'rot', 'blight', 'leaf']):
                        found = True
                        break
                    # fallback check using RAG ID
                    # e.g., 'cabbage_bacterial_spot_rot'
                    
            if not found:
                # Let's do a loose check against rag_ids
                for rid in rag_ids:
                    if l_crop in rid.replace('_',' ') and l_disease.split()[0] in rid.replace('_',' '):
                        found = True
                        break
            if not found:
                missing.append(label)

    print("Model Labels (excluding 'healthy'):", len([l for l in model_labels if 'healthy' not in l.lower()]))
    print("RAG Entries mapped:", len(rag_disease_names))
    
    if not missing:
        print("All labels seem to be present in RAG data!")
    else:
        print(f"Potentially missing labels ({len(missing)}):")
        for m in missing:
            print(f" - {m}")

check_missing_labels()
