import os
import json
import re

d = 'RAG'
diseases = {}

for f in os.listdir(d):
    if not f.endswith('.txt'):
        continue
    path = os.path.join(d, f)
    if os.path.getsize(path) == 0:
        continue
    with open(path, 'r', encoding='utf-8-sig') as file:
        content = file.read().strip()
        if not content:
            continue
        content = re.sub(r',\s*\}', '}', content)
        content = re.sub(r',\s*\]', ']', content)
        try:
            data = json.loads(content)
            for obj in data:
                crop = obj.get('crop', {}).get('common_name', 'Unknown')
                disease = obj.get('disease', {}).get('name', 'Unknown')
                diseases.setdefault(crop, set()).add(disease)
        except Exception as e:
            pass

for crop, disease_list in sorted(diseases.items()):
    print(f"\n**{crop}**:")
    for d in sorted(disease_list):
        print(f"- {d}")
