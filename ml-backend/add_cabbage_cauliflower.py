import json
import os

def append_to_rag(file_name, new_data):
    path = os.path.join('RAG', file_name)
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data.extend(new_data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

cabbage_bacterial_spot = {
    "id": "cabbage_bacterial_spot_rot",
    "crop": {
      "common_name": "Cabbage", "english_name": "Cabbage", "scientific_name": "Brassica oleracea", "local_names": ["Patta Gobhi"], "crop_category": "Vegetable"
    },
    "disease": {
      "name": "Bacterial Spot Rot", "category": "Bacterial", "pathogen_or_cause": ["Pectobacterium carotovorum"], "affected_parts": ["Leaves", "Heads", "Stems"], "disease_stage": "Vegetative to Mature"
    },
    "symptoms": {
      "early_stage": ["Small water-soaked spots on leaves."],
      "middle_stage": ["Spots enlarge, become sunken, soft and mushy."],
      "severe_stage": ["Head turns into a foul-smelling mushy rot. Plant collapses."],
      "visible_signs": ["Foul smell, soft decaying tissue, watery spots."],
      "farmer_reported_signs": ["Cabbage head rotting and smelling bad", "Mushy spots on leaves"]
    },
    "visual_identification": {
      "color_changes": ["Translucent", "Brown to black mush"], "spot_or_patch_shape": "Irregular expanding soft spots", "pattern": "Wet decay", "location_on_plant": "Anywhere, primarily head and stem", "starts_from": "Wounds or insect damage", "progression": "Small spots -> Soft rot -> Complete collapse", "image_clues": ["Look for wet, mushy decay on cabbage head"]
    },
    "similar_diseases_or_issues": [
      {"name": "Black Rot", "difference": "Black rot has V-shaped yellow margins and black veins without initial mushy decay.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Warm, wet", "High rainfall"], "temperature_range": "25-30C", "humidity_level": ">90%", "season": "Monsoon", "soil_conditions": ["Waterlogged"], "field_conditions": ["Poor drainage"], "irrigation_conditions": ["Overhead sprinkler"]
    },
    "spread": {
      "spread_by": ["Splashing water", "Insects", "Contaminated tools"], "source_of_infection": ["Soil", "Crop debris"], "survival_method": "In soil or plant residue", "spread_speed": "Fast", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "Low", "description": "Minor water-soaked spots.", "field_indicator": "<5% infected.", "recommended_action": "Improve drainage, remove affected leaves."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use certified disease-free seeds."], "field_management": ["Avoid wounding plants."], "irrigation_management": ["Avoid overhead irrigation."], "soil_management": ["Improve drainage."], "crop_rotation": ["Rotate with cereals."], "sanitation": ["Destroy infected debris."], "monitoring": ["Check for rot after heavy rains."]
    },
    "management": {
      "immediate_action": ["Remove and destroy infected plants."], "cultural_control": ["Sanitize tools."], "organic_control": ["Copper-based sprays."], "biological_control": ["Bacillus species."], "chemical_control": [{"active_ingredient": "Copper Hydroxide", "product_type": "Bactericide", "dose": "2g/L", "application_method": "Spray", "spray_interval": "7 days", "pre_harvest_interval": "0 days", "safety_note": "Apply carefully."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A bacterial disease causing mushy, smelly rot.", "what_to_do_now": ["Remove rotting plants immediately."], "what_not_to_do": ["Don't leave rotting cabbage in the field.", "Don't water from above."], "when_to_call_expert": ["If rot spreads rapidly."], "risk_warning": "Can destroy entire heads quickly."
    },
    "model_support": {
      "classification_labels": ["cabbage_bacterial_spot_rot"], "segmentation_labels": ["soft_rot_patch"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["Symptoms resemble chemical burn."], "image_quality_requirements": ["Clear focus on the rot."]
    },
    "rag_chunks": [],
    "geo_outbreak_data": {"location_level": "District", "risk_radius": "5km", "report_count_threshold": "3", "outbreak_alert_message": "Bacterial Soft Rot alert.", "nearby_farm_advice": ["Improve drainage."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

cabbage_aphid = {
    "id": "cabbage_aphid_colony",
    "crop": cabbage_bacterial_spot["crop"],
    "disease": {
      "name": "Aphid Colony", "category": "Pest", "pathogen_or_cause": ["Brevicoryne brassicae"], "affected_parts": ["Leaves", "Tender shoots"], "disease_stage": "All stages"
    },
    "symptoms": {
      "early_stage": ["Small gray-green insects on undersides of leaves."],
      "middle_stage": ["Leaves turn yellow, crinkle, and cup. Sticky honeydew appears."],
      "severe_stage": ["Stunted growth, sooty mold covers leaves, dense colonies."],
      "visible_signs": ["Mealy gray aphid clusters, honeydew, sooty mold."],
      "farmer_reported_signs": ["Small bugs under leaves", "Sticky black leaves"]
    },
    "visual_identification": {
      "color_changes": ["Yellowing", "Black sooty mold"], "spot_or_patch_shape": "Clusters of insects", "pattern": "Dense colonies", "location_on_plant": "Undersides of leaves, shoots", "starts_from": "Tender new growth", "progression": "A few aphids -> Huge colonies -> Plant stunting", "image_clues": ["Look for waxy gray insect clusters."]
    },
    "similar_diseases_or_issues": [
      {"name": "Whitefly", "difference": "Whiteflies fly around when disturbed, aphids do not.", "confusion_risk": "Low"}
    ],
    "favorable_conditions": {
      "weather": ["Dry, warm"], "temperature_range": "20-25C", "humidity_level": "<60%", "season": "Spring/Autumn", "soil_conditions": ["N/A"], "field_conditions": ["Weed presence"], "irrigation_conditions": ["Water stress"]
    },
    "spread": {
      "spread_by": ["Wind (winged aphids)"], "source_of_infection": ["Weeds", "Nearby crops"], "survival_method": "Eggs or adults on weeds", "spread_speed": "Fast", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "Low", "description": "Few aphids.", "field_indicator": "<10% plants.", "recommended_action": "Use insecticidal soap."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Inspect seedlings."], "field_management": ["Remove weeds."], "irrigation_management": ["Avoid water stress."], "soil_management": ["Avoid excess nitrogen."], "crop_rotation": ["Rotate with non-brassicas."], "sanitation": ["Destroy residues."], "monitoring": ["Regularly check undersides of leaves."]
    },
    "management": {
      "immediate_action": ["Spray neem oil or soap."], "cultural_control": ["Use yellow sticky traps."], "organic_control": ["Neem oil 3%."], "biological_control": ["Ladybugs, lacewings."], "chemical_control": [{"active_ingredient": "Imidacloprid", "product_type": "Insecticide", "dose": "0.5mL/L", "application_method": "Spray", "spray_interval": "10 days", "pre_harvest_interval": "7 days", "safety_note": "Apply strictly."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "Aphids suck sap and weaken the plant.", "what_to_do_now": ["Spray neem oil."], "what_not_to_do": ["Don't over-fertilize with nitrogen."], "when_to_call_expert": ["If populations explode."], "risk_warning": "Can spread viruses."
    },
    "model_support": {
      "classification_labels": ["cabbage_aphid_colony"], "segmentation_labels": ["aphid_cluster"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Macro shot of insects."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "5km", "report_count_threshold": "3", "outbreak_alert_message": "Aphid alert.", "nearby_farm_advice": ["Spray neem."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

cabbage_club_root = {
    "id": "cabbage_club_root",
    "crop": cabbage_bacterial_spot["crop"],
    "disease": {
      "name": "Club Root", "category": "Fungal-like", "pathogen_or_cause": ["Plasmodiophora brassicae"], "affected_parts": ["Roots"], "disease_stage": "All stages"
    },
    "symptoms": {
      "early_stage": ["Wilting during sunny days, recovery at night."],
      "middle_stage": ["Stunted growth, pale green or yellow leaves."],
      "severe_stage": ["Large, swollen, distorted 'clubs' or galls on roots. Plant dies."],
      "visible_signs": ["Swollen roots, daytime wilting."],
      "farmer_reported_signs": ["Roots are swollen like a club", "Plants wilt in the sun even with wet soil"]
    },
    "visual_identification": {
      "color_changes": ["Yellowing foliage"], "spot_or_patch_shape": "Swollen galls on roots", "pattern": "Systemic root distortion", "location_on_plant": "Roots", "starts_from": "Root hairs", "progression": "Root swelling -> Nutrient blockage -> Wilting", "image_clues": ["Look for swollen distorted roots when pulled out."]
    },
    "similar_diseases_or_issues": [
      {"name": "Root-knot nematode", "difference": "Nematode galls are smaller and bead-like, while club root forms massive, solid swellings.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Cool, wet"], "temperature_range": "15-20C", "humidity_level": "High", "season": "Winter", "soil_conditions": ["Acidic (pH < 7.0)", "Poorly drained"], "field_conditions": ["Infested soil"], "irrigation_conditions": ["Waterlogged"]
    },
    "spread": {
      "spread_by": ["Soil movement", "Tools", "Water runoff"], "source_of_infection": ["Soil resting spores"], "survival_method": "Spores in soil for up to 10 years", "spread_speed": "Slow (field-wise) but devastating", "nearby_crop_risk": "High for brassicas"
    },
    "severity_levels": [
      {"level": "High", "description": "Severe wilting.", "field_indicator": "Root galls.", "recommended_action": "Uproot and destroy."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use clean transplants."], "field_management": ["Lime soil to pH 7.2."], "irrigation_management": ["Improve drainage."], "soil_management": ["Add agricultural lime."], "crop_rotation": ["Rotate non-brassicas for 5+ years."], "sanitation": ["Clean boots and tools."], "monitoring": ["Check roots of wilting plants."]
    },
    "management": {
      "immediate_action": ["Remove infected plants."], "cultural_control": ["Liming."], "organic_control": ["None effective once infected."], "biological_control": ["None highly effective."], "chemical_control": [], "expert_recommendation_required": True
    },
    "farmer_advice": {
      "simple_explanation": "A soil pathogen that deforms roots and starves the plant.", "what_to_do_now": ["Apply lime to soil for future crops."], "what_not_to_do": ["Don't move soil from infested fields.", "Don't plant brassicas here again soon."], "when_to_call_expert": ["Always, to confirm clubroot."], "risk_warning": "Pathogen lives 10+ years in soil."
    },
    "model_support": {
      "classification_labels": ["cabbage_club_root"], "segmentation_labels": ["swollen_root_gall"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["Nematode suspected."], "image_quality_requirements": ["Photo of washed roots."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "Field", "risk_radius": "0km", "report_count_threshold": "1", "outbreak_alert_message": "Clubroot detected.", "nearby_farm_advice": ["Sanitize machinery."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

cabbage_ring_spot = {
    "id": "cabbage_ring_spot",
    "crop": cabbage_bacterial_spot["crop"],
    "disease": {
      "name": "Ring Spot", "category": "Fungal", "pathogen_or_cause": ["Mycosphaerella brassicicola"], "affected_parts": ["Leaves"], "disease_stage": "Mid to Late"
    },
    "symptoms": {
      "early_stage": ["Small dark circular spots on older leaves."],
      "middle_stage": ["Spots expand to 2-3cm with tiny black specks arranged in concentric rings."],
      "severe_stage": ["Leaves turn yellow and drop. Lesions on stems and seed pods."],
      "visible_signs": ["Concentric rings of black specks within a spot."],
      "farmer_reported_signs": ["Circles with black dots on leaves", "Leaves dying early"]
    },
    "visual_identification": {
      "color_changes": ["Dark brown", "Yellow halo"], "spot_or_patch_shape": "Circular with concentric rings", "pattern": "Target-like with black dots", "location_on_plant": "Older leaves first", "starts_from": "Lower leaves", "progression": "Spots -> Yellowing -> Defoliation", "image_clues": ["Look for tiny black pinhead dots inside the spots."]
    },
    "similar_diseases_or_issues": [
      {"name": "Alternaria Leaf Spot", "difference": "Alternaria has concentric dark rings but lacks the distinct tiny black fruiting bodies (pycnidia) of ring spot.", "confusion_risk": "High"}
    ],
    "favorable_conditions": {
      "weather": ["Cool, moist"], "temperature_range": "15-20C", "humidity_level": ">90%", "season": "Winter/Spring", "soil_conditions": ["N/A"], "field_conditions": ["Dense planting"], "irrigation_conditions": ["Overhead irrigation"]
    },
    "spread": {
      "spread_by": ["Wind", "Rain splashes"], "source_of_infection": ["Crop debris", "Seeds"], "survival_method": "Infected debris", "spread_speed": "Moderate", "nearby_crop_risk": "Medium"
    },
    "severity_levels": [
      {"level": "Medium", "description": "Spots with rings.", "field_indicator": "10% foliage.", "recommended_action": "Spray fungicide."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Hot water seed treatment."], "field_management": ["Weed control."], "irrigation_management": ["Drip irrigation."], "soil_management": ["Good drainage."], "crop_rotation": ["2-3 year rotation."], "sanitation": ["Destroy debris."], "monitoring": ["Scout older leaves."]
    },
    "management": {
      "immediate_action": ["Remove infected leaves."], "cultural_control": ["Sanitation."], "organic_control": ["Copper fungicide."], "biological_control": ["N/A"], "chemical_control": [{"active_ingredient": "Chlorothalonil", "product_type": "Fungicide", "dose": "2g/L", "application_method": "Spray", "spray_interval": "10 days", "pre_harvest_interval": "7 days", "safety_note": "Apply preventatively."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A fungal disease causing ringed spots with black dots on leaves.", "what_to_do_now": ["Spray fungicide like Chlorothalonil."], "what_not_to_do": ["Don't use overhead sprinklers."], "when_to_call_expert": ["If confusion with Alternaria exists."], "risk_warning": "Can reduce yield if defoliation is severe."
    },
    "model_support": {
      "classification_labels": ["cabbage_ring_spot"], "segmentation_labels": ["ring_spot_lesion"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Macro of the spot showing black dots."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "5km", "report_count_threshold": "3", "outbreak_alert_message": "Ring spot alert.", "nearby_farm_advice": ["Apply fungicide."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

cauliflower_bacterial_spot = cabbage_bacterial_spot.copy()
cauliflower_bacterial_spot["id"] = "cauliflower_bacterial_spot_rot"
cauliflower_bacterial_spot["crop"] = {
      "common_name": "Cauliflower", "english_name": "Cauliflower", "scientific_name": "Brassica oleracea var. botrytis", "local_names": ["Phool Gobhi"], "crop_category": "Vegetable"
}

append_to_rag('Cabbage.txt', [cabbage_bacterial_spot, cabbage_aphid, cabbage_club_root, cabbage_ring_spot])
append_to_rag('Cauliflower.txt', [cauliflower_bacterial_spot])
print("Added Cabbage and Cauliflower diseases.")
