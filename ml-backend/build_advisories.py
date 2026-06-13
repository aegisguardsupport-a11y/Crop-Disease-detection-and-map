import os
import json
import re
from pathlib import Path

# Paths
WORKSPACE_DIR = Path("c:/Users/techb/OneDrive/Desktop/cpl_hackathon")
RAG_DIR = WORKSPACE_DIR / "RAG"
LABELS_PATH = WORKSPACE_DIR / "Crop_disease_prediction_online" / "exports" / "cpl_id_to_label.json"
OUTPUT_DIR = WORKSPACE_DIR / "cpl_offline_kit" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "advisories.json"

CROP_MAP = {
    "bhindi": "Bhindi",
    "blackgram": "Blackgram",
    "brinjal": "Brinjal",
    "cabbage": "Cabbage",
    "cauliflower": "Cauliflower",
    "chilli": "Chilli",
    "cotton": "Cotton",
    "cowpea": "Cowpea",
    "groundnut": "Groundnut",
    "maize": "Maize",
    "onion": "Onion",
    "pigeonpea": "Pigeonpea",
    "ragi": "Ragi",
    "rice": "Rice",
    "sorghum": "Sorghum",
    "soyabean": "Soyabean",
    "sugarcane": "Sugarcane",
    "sunflower": "Sunflower",
    "tomato": "Tomato",
    "wheat": "Wheat"
}

# Manual mapping overrides for label -> RAG disease name
MANUAL_OVERRIDES = {
    "blackgram::Leaf_Crinckle": "Leaf Crinkle",
    "blackgram::Powdery_Mildew": "Powdery_Mildew",
    "blackgram::Yellow_Mosaic": "Yellow_Mosaic",
    "cowpea::Bacterial_wilt": "Bacterial_wilt",
    "cowpea::Mosaic_virus": "Mosaic_virus",
    "cowpea::Septoria_leaf_spot": "Septoria_leaf_spot",
    "cowpea::healthy": "healthy",
    "groundnut::early_leaf_spot_1": "early_leaf_spot_1",
    "groundnut::early_rust_1": "early_rust_1",
    "groundnut::healthy_leaf_1": "healthy_leaf_1",
    "groundnut::late_leaf_spot_1": "late_leaf_spot_1",
    "groundnut::nutrition_deficiency_1": "nutrition_deficiency_1",
    "groundnut::rust_1": "rust_1",
    "rice::Bacterialblight": "Bacterial Leaf Blight",
    "rice::Bacterial_leaf_blight": "Bacterial Leaf Blight",
    "rice::Brownspot": "Brown Spot",
    "rice::Brown_spot": "Brown Spot",
    "rice::Leafsmut": "Leaf Smut",
    "rice::Leaf_smut": "Leaf Smut",
    "sorghum::AnthracnoseRed Rot": "Anthracnose and Red Rot",
    "sorghum::Cereal Grain molds (White Fungi)t": "Cereal Grain Molds (White and Pink Fungi)",
    "sorghum::Covered Kernel smut (sori creamy)t": "Covered Kernel Smut (Sori Creamy / Grain Smut)",
    "sorghum::Head Smut (White Spreaded)t": "Head Smut (White Spreaded / Panicle Destruction)",
    "sorghum::loose smut (black)": "Loose Smut (Black / Spontaneous Rupture)",
    "soyabean::Mossaic Virus": "Soybean Mosaic Virus",
    "soyabean::Southern blight": "Southern Blight",
    "soyabean::Sudden Death Syndrone": "Sudden Death Syndrome",
    "soyabean::Yellow Mosaic": "Yellow Mosaic Virus",
    "soyabean::bacterial_blight": "Bacterial Blight",
    "soyabean::brown_spot": "Septoria Brown Spot",
    "soyabean::septoria": "Septoria Brown Spot",
    "wheat::BlackPoint": "Black Point / Kernel Smudge",
    "wheat::FusariumFootRot": "Fusarium Foot Rot and Crown Rot",
    "wheat::LeafBlight": "Leaf Blight / Helminthosporium Leaf Blight Complex",
    "wheat::WheatBlast": "Wheat Blast",
    "maize::Maize grasshoper": "Maize Grasshopper Infestation",
    "tomato::Tomato___Spider_mites Two-spotted_spider_mite": "Two-Spotted Spider Mites Infestation",
    "onion::Alternaria_D": "Alternaria_D",
    "onion::Bulb_blight-D": "Bulb_blight-D",
    "onion::Caterpillar-P": "Caterpillar-P",
    "onion::Fusarium-D": "Fusarium-D",
    "onion::Virosis-D": "Virosis-D",
    "ragi::downy": "downy",
    "ragi::mottle": "mottle",
    "ragi::seedling": "seedling",
    "ragi::smut": "smut",
    "ragi::wilt": "wilt",
    "pigeonpea::Leaf_Spot": "Cercospora Leaf Spot",
    "pigeonpea::Leaf_webber": "Leaf Webber / Pod Borer Complex",
    "pigeonpea::Sterilic_mosaic": "Sterility Mosaic Disease"
}

def clean_json_string(s):
    s = s.strip()
    # Remove markdown formatting
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    s = s.strip()
    
    # Remove trailing commas in objects and arrays
    s = re.sub(r',\s*([\]}])', r'\1', s)
    return s

def clean_name(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9]', ' ', name)
    name = " ".join(name.split())
    # strip crop prefixes
    for k in CROP_MAP.keys():
        if name.startswith(k + " "):
            name = name[len(k)+1:]
    return name.strip()

def main():
    with open(LABELS_PATH, "r") as f:
        labels = json.load(f)
    
    advisories = {}
    mismatches = []
    
    # Load and clean all RAG files
    rag_data = {}
    for crop_prefix, rag_file_prefix in CROP_MAP.items():
        rag_file_path = RAG_DIR / f"{rag_file_prefix}.txt"
        if not rag_file_path.exists():
            print(f"Warning: RAG file {rag_file_path} not found")
            rag_data[rag_file_prefix] = []
            continue
            
        with open(rag_file_path, "r", encoding="utf-8") as f_rag:
            raw_content = f_rag.read()
            cleaned_content = clean_json_string(raw_content)
            try:
                rag_data[rag_file_prefix] = json.loads(cleaned_content)
                print(f"Loaded {rag_file_prefix} successfully with {len(rag_data[rag_file_prefix])} entries.")
            except Exception as e:
                print(f"Error parsing {rag_file_prefix}: {e}")
                # Try to extract JSON array if there is noise
                try:
                    # find first [ and last ]
                    start = cleaned_content.find('[')
                    end = cleaned_content.rfind(']')
                    if start != -1 and end != -1:
                        json_str = cleaned_content[start:end+1]
                        rag_data[rag_file_prefix] = json.loads(json_str)
                        print(f"Recovered {rag_file_prefix} with {len(rag_data[rag_file_prefix])} entries.")
                    else:
                        rag_data[rag_file_prefix] = []
                except Exception as e2:
                    print(f"Failed to recover {rag_file_prefix}: {e2}")
                    rag_data[rag_file_prefix] = []

    # Map labels
    for label_id, full_label in labels.items():
        crop_prefix, disease_part = full_label.split("::")
        
        # Check if healthy
        is_healthy = "healthy" in disease_part.lower() or "fresh leaf" in disease_part.lower()
        
        if is_healthy:
            advisories[label_id] = {
                "label": full_label,
                "crop": crop_prefix.capitalize(),
                "disease": "Healthy",
                "is_healthy": True,
                "symptoms": {
                    "explanation": f"No disease symptoms detected. The {crop_prefix} crop appears healthy and robust.",
                    "visible_signs": []
                },
                "prevention": [
                    "Maintain regular weeding and optimal crop spacing for air circulation.",
                    "Apply recommended balanced organic/chemical fertilizers based on soil health.",
                    "Water appropriately (preferably drip or morning furrow) to prevent waterlogging and reduce leaf wetness time.",
                    "Inspect leaves, stems, and fruits regularly to catch any early disease or pest symptoms."
                ],
                "organic_control": ["Not applicable for healthy crops. Maintain organic bio-fertilizers or neem sprays preventatively if necessary."],
                "chemical_control": [],
                "farmer_advice": {
                    "simple_explanation": "Your crop is healthy! No disease spots, wilts, or rot signs are detected.",
                    "what_to_do_now": [
                        "Keep up standard agronomic and irrigation practices.",
                        "Continue monitoring the field twice a week."
                    ],
                    "what_not_to_do": [
                        "Do not apply protective fungicides or bactericides unless a local outbreak warning is active."
                    ]
                }
            }
            continue

        rag_file_prefix = CROP_MAP[crop_prefix]
        diseases_list = rag_data[rag_file_prefix]
        
        matched_obj = None
        
        # Check manual overrides first
        override_name = MANUAL_OVERRIDES.get(full_label)
        if override_name:
            for d in diseases_list:
                d_name = d.get("disease", {}).get("name", "")
                if d_name.strip().lower() == override_name.strip().lower() or d.get("id", "").strip().lower() == override_name.strip().lower():
                    matched_obj = d
                    break
        
        # Try match by name or id
        if not matched_obj:
            cleaned_label = clean_name(disease_part)
            for d in diseases_list:
                d_name = d.get("disease", {}).get("name", "")
                d_id = d.get("id", "")
                if clean_name(d_name) == cleaned_label or clean_name(d_id) == cleaned_label:
                    matched_obj = d
                    break
                    
        # Try substring match
        if not matched_obj:
            cleaned_label = clean_name(disease_part)
            for d in diseases_list:
                d_name = d.get("disease", {}).get("name", "")
                c_d_name = clean_name(d_name)
                if c_d_name in cleaned_label or cleaned_label in c_d_name:
                    matched_obj = d
                    break

        if not matched_obj:
            mismatches.append((full_label, disease_part, [d.get("disease", {}).get("name", d.get("id", "")) for d in diseases_list]))
            # Fallback
            advisories[label_id] = {
                "label": full_label,
                "crop": crop_prefix.capitalize(),
                "disease": disease_part,
                "is_healthy": False,
                "symptoms": {
                    "explanation": f"Symptoms of {disease_part} on {crop_prefix}.",
                    "visible_signs": []
                },
                "prevention": [
                    "Practice standard crop rotation.",
                    "Use certified disease-free seeds.",
                    "Ensure proper soil drainage."
                ],
                "organic_control": ["Apply organic controls if symptoms appear early."],
                "chemical_control": [],
                "farmer_advice": {
                    "simple_explanation": f"{disease_part} is a disease affecting {crop_prefix}.",
                    "what_to_do_now": ["Consult a local agricultural officer for diagnosis and treatment options.", "Rogue out infected leaves/stems immediately."],
                    "what_not_to_do": ["Do not save seed from affected crops."]
                }
            }
        else:
            d_obj = matched_obj
            symptoms = d_obj.get("symptoms", {})
            symptom_explanation = (
                "Early Stage: " + " ".join(symptoms.get("early_stage", [])) + "\n" +
                "Middle Stage: " + " ".join(symptoms.get("middle_stage", [])) + "\n" +
                "Severe Stage: " + " ".join(symptoms.get("severe_stage", []))
            )
            
            prevention_data = d_obj.get("prevention", {})
            prevention_list = []
            for key, val in prevention_data.items():
                if isinstance(val, list):
                    prevention_list.extend(val)
                elif isinstance(val, str):
                    prevention_list.append(val)
            
            mgmt = d_obj.get("management", {})
            org_controls = []
            if mgmt.get("organic_control"):
                org_controls.extend(mgmt.get("organic_control"))
            if mgmt.get("biological_control"):
                org_controls.extend(mgmt.get("biological_control"))
                
            chem_list = []
            for chem in mgmt.get("chemical_control", []):
                chem_list.append({
                    "active_ingredient": chem.get("active_ingredient", ""),
                    "product_type": chem.get("product_type", ""),
                    "dose": chem.get("dose", ""),
                    "application_method": chem.get("application_method", ""),
                    "safety_note": chem.get("safety_note", "")
                })
                
            farmer_adv = d_obj.get("farmer_advice", {})
            
            advisories[label_id] = {
                "label": full_label,
                "crop": crop_prefix.capitalize(),
                "disease": d_obj.get("disease", {}).get("name", disease_part),
                "is_healthy": False,
                "symptoms": {
                    "explanation": symptom_explanation,
                    "visible_signs": symptoms.get("visible_signs", [])
                },
                "prevention": prevention_list[:8],
                "organic_control": org_controls,
                "chemical_control": chem_list,
                "farmer_advice": {
                    "simple_explanation": farmer_adv.get("simple_explanation", ""),
                    "what_to_do_now": farmer_adv.get("what_to_do_now", []),
                    "what_not_to_do": farmer_adv.get("what_not_to_do", [])
                }
            }
            
    # Save output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f_out:
        json.dump(advisories, f_out, indent=2, ensure_ascii=False)
        
    print(f"\nSuccessfully generated advisories.json with {len(advisories)} entries.")
    if mismatches:
        print(f"\n--- Warning: {len(mismatches)} diseases could not be cleanly mapped and used fallbacks ---")
        for full, part, options in mismatches:
            print(f"Label: {full}")
            print(f"Available options in RAG: {options}\n")

if __name__ == "__main__":
    main()
