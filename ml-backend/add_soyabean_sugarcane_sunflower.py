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

soyabean_ferrugen = {
    "id": "soyabean_ferrugen",
    "crop": {
      "common_name": "Soyabean", "english_name": "Soybean", "scientific_name": "Glycine max", "local_names": ["Soyabean"], "crop_category": "Legume"
    },
    "disease": {
      "name": "Ferrugen (Soybean Rust)", "category": "Fungal", "pathogen_or_cause": ["Phakopsora pachyrhizi"], "affected_parts": ["Leaves"], "disease_stage": "Flowering to Maturity"
    },
    "symptoms": {
      "early_stage": ["Tiny brown or brick-red spots on the lower leaves."],
      "middle_stage": ["Spots expand, form raised pustules on the underside of leaves."],
      "severe_stage": ["Pustules burst, releasing rust-colored spores. Leaves turn yellow, dry up, and drop prematurely."],
      "visible_signs": ["Rust colored powdery spores on leaf undersides."],
      "farmer_reported_signs": ["Rusty powder on the bottom of leaves", "Leaves turning yellow and falling off"]
    },
    "visual_identification": {
      "color_changes": ["Brick red", "Yellow"], "spot_or_patch_shape": "Small pustules", "pattern": "Dense clusters on underside", "location_on_plant": "Lower canopy progressing upwards", "starts_from": "Lower leaves", "progression": "Spots -> Pustules -> Yellowing -> Defoliation", "image_clues": ["Look for raised rusty pustules on the underside of the leaf."]
    },
    "similar_diseases_or_issues": [
      {"name": "Brown Spot (Septoria)", "difference": "Brown spot lacks the raised rusty pustules on the underside.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Cool, moist", "Cloudy"], "temperature_range": "15-28C", "humidity_level": "High (prolonged leaf wetness)", "season": "Late Summer/Monsoon", "soil_conditions": ["N/A"], "field_conditions": ["Dense canopy"], "irrigation_conditions": ["Frequent rain or dew"]
    },
    "spread": {
      "spread_by": ["Wind (long distances)"], "source_of_infection": ["Spores blown from warmer regions"], "survival_method": "Living hosts", "spread_speed": "Very Fast", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "High", "description": "Rapid spread of pustules.", "field_indicator": "Lower canopy yellowing.", "recommended_action": "Apply fungicide immediately."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use tolerant varieties."], "field_management": ["Wider row spacing."], "irrigation_management": ["Avoid overhead watering."], "soil_management": ["Balanced nutrition."], "crop_rotation": ["N/A"], "sanitation": ["N/A"], "monitoring": ["Scout lower canopy frequently after flowering."]
    },
    "management": {
      "immediate_action": ["Spray fungicide at first sign."], "cultural_control": ["None very effective once spores arrive."], "organic_control": ["Limited effectiveness."], "biological_control": ["N/A"], "chemical_control": [{"active_ingredient": "Azoxystrobin", "product_type": "Fungicide", "dose": "1mL/L", "application_method": "Spray", "spray_interval": "14 days", "pre_harvest_interval": "21 days", "safety_note": "Ensure underside coverage."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A very fast-spreading fungus that causes rusty powder on the undersides of leaves.", "what_to_do_now": ["Spray a strobilurin/triazole fungicide."], "what_not_to_do": ["Don't wait; rust spreads incredibly fast."], "when_to_call_expert": ["If unsure if it is rust or brown spot."], "risk_warning": "Can cause massive yield loss if ignored."
    },
    "model_support": {
      "classification_labels": ["soyabean_ferrugen"], "segmentation_labels": ["rust_pustule"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Macro shot of leaf underside."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "State", "risk_radius": "100km", "report_count_threshold": "1", "outbreak_alert_message": "Soybean Rust in your region. Spray preventatively.", "nearby_farm_advice": ["Scout and spray."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""}
}

soyabean_powdery_mildew = {
    "id": "soyabean_powdery_mildew",
    "crop": soyabean_ferrugen["crop"],
    "disease": {
      "name": "Powdery Mildew", "category": "Fungal", "pathogen_or_cause": ["Erysiphe diffusa"], "affected_parts": ["Leaves", "Stems", "Pods"], "disease_stage": "Late Season"
    },
    "symptoms": {
      "early_stage": ["Small, circular white to light-gray 'talcum-powder-like' patches on upper leaf surfaces."],
      "middle_stage": ["Patches enlarge and cover entire leaves (both sides)."],
      "severe_stage": ["Leaves turn yellow, brown, and drop. Pods may be affected, leading to shriveled seeds."],
      "visible_signs": ["White powdery growth on leaves."],
      "farmer_reported_signs": ["White powder coating the leaves"]
    },
    "visual_identification": {
      "color_changes": ["White", "Yellowing"], "spot_or_patch_shape": "Irregular powdery patches", "pattern": "Dusting effect", "location_on_plant": "Upper leaves mostly", "starts_from": "Upper surface", "progression": "Spots -> Full coverage -> Yellowing -> Defoliation", "image_clues": ["Look for white talcum powder-like dusting."]
    },
    "similar_diseases_or_issues": [
      {"name": "Downy Mildew", "difference": "Downy mildew is yellowish on top and has fuzzy gray growth ONLY on the bottom, while Powdery is white on top.", "confusion_risk": "Low"}
    ],
    "favorable_conditions": {
      "weather": ["Cool, cloudy"], "temperature_range": "18-24C", "humidity_level": "Low to Moderate", "season": "Late season", "soil_conditions": ["N/A"], "field_conditions": ["Late planted crops"], "irrigation_conditions": ["N/A"]
    },
    "spread": {
      "spread_by": ["Wind"], "source_of_infection": ["Wind-blown spores"], "survival_method": "Alternate hosts", "spread_speed": "Moderate", "nearby_crop_risk": "Medium"
    },
    "severity_levels": [
      {"level": "Medium", "description": "White powder on leaves.", "field_indicator": "Usually occurs late, low yield impact.", "recommended_action": "Spray only if severe."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Resistant varieties."], "field_management": ["Plant on time (avoid late planting)."], "irrigation_management": ["N/A"], "soil_management": ["N/A"], "crop_rotation": ["Not highly effective."], "sanitation": ["N/A"], "monitoring": ["Scout late-season."]
    },
    "management": {
      "immediate_action": ["Often not economical to spray late season."], "cultural_control": ["None."], "organic_control": ["Sulfur or neem oil."], "biological_control": ["N/A"], "chemical_control": [{"active_ingredient": "Wettable Sulfur", "product_type": "Fungicide", "dose": "3g/L", "application_method": "Spray", "spray_interval": "14 days", "pre_harvest_interval": "14 days", "safety_note": "Do not spray in extreme heat."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A fungus that coats leaves in white powder, usually late in the season.", "what_to_do_now": ["Evaluate if spraying is worth the cost if harvest is near."], "what_not_to_do": ["Don't spray sulfur on very hot days."], "when_to_call_expert": ["If symptoms appear very early in the season."], "risk_warning": "Often cosmetic unless infection happens early."
    },
    "model_support": {
      "classification_labels": ["soyabean_powdery_mildew"], "segmentation_labels": ["powdery_patch"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Clear shot of the white powder."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "10km", "report_count_threshold": "3", "outbreak_alert_message": "", "nearby_farm_advice": []},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""}
}

sugarcane_mosaic = {
    "id": "sugarcane_mosaic",
    "crop": {
      "common_name": "Sugarcane", "english_name": "Sugarcane", "scientific_name": "Saccharum officinarum", "local_names": ["Ganna"], "crop_category": "Cash Crop"
    },
    "disease": {
      "name": "Mosaic", "category": "Viral", "pathogen_or_cause": ["Sugarcane Mosaic Virus (SCMV)"], "affected_parts": ["Leaves", "Stalks"], "disease_stage": "Early growth"
    },
    "symptoms": {
      "early_stage": ["Mottled appearance on younger growing leaves with light green to yellow patches/stripes."],
      "middle_stage": ["Plant appears pale, chlorotic, and stunted. Fewer tillers."],
      "severe_stage": ["Yellow stripes on leaf sheaths. Necrotic lesions on stalks. Stems may split."],
      "visible_signs": ["Yellow/green mottling on young leaves, stunted growth."],
      "farmer_reported_signs": ["Leaves look streaky yellow and green", "Plant is not growing well"]
    },
    "visual_identification": {
      "color_changes": ["Light green", "Yellow"], "spot_or_patch_shape": "Irregular patches/stripes", "pattern": "Mosaic/mottled", "location_on_plant": "Young leaves", "starts_from": "New growth", "progression": "Mottling -> Stunting -> Yield loss", "image_clues": ["Look for the classic mosaic mottled pattern on the newest leaves."]
    },
    "similar_diseases_or_issues": [
      {"name": "Nutrient deficiency", "difference": "Nutrient deficiency is usually uniform yellowing, while mosaic is distinctly mottled/patchy.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Warm"], "temperature_range": "25-35C", "humidity_level": "Variable", "season": "Spring/Summer", "soil_conditions": ["N/A"], "field_conditions": ["Presence of aphids"], "irrigation_conditions": ["N/A"]
    },
    "spread": {
      "spread_by": ["Aphids", "Infected setts (cuttings)", "Tools"], "source_of_infection": ["Infected seed canes"], "survival_method": "In living plants", "spread_speed": "Moderate", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "Medium", "description": "Mosaic pattern on leaves.", "field_indicator": "Stunted tillers.", "recommended_action": "Rogue out infected plants."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use certified disease-free setts.", "Aerated Steam Therapy (AST) at 56C."], "field_management": ["Remove infected clumps (roguing)."], "irrigation_management": ["N/A"], "soil_management": ["Adequate fertilizer."], "crop_rotation": ["N/A"], "sanitation": ["Sanitize cutting knives."], "monitoring": ["Scout for aphids and mottled leaves."]
    },
    "management": {
      "immediate_action": ["Rogue and destroy infected plants."], "cultural_control": ["Vector control."], "organic_control": ["Release green lacewings for aphids."], "biological_control": ["Chrysoperla carnea."], "chemical_control": [{"active_ingredient": "Imidacloprid", "product_type": "Insecticide", "dose": "0.5mL/L", "application_method": "Spray", "spray_interval": "15 days", "pre_harvest_interval": "N/A", "safety_note": "Target aphids."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A virus transmitted by aphids and infected cuttings that stunts plant growth.", "what_to_do_now": ["Remove the infected plants completely."], "what_not_to_do": ["Don't use cuttings from this field for next planting."], "when_to_call_expert": ["If you see widespread mottling."], "risk_warning": "Cannot be cured; prevention is key."
    },
    "model_support": {
      "classification_labels": ["sugarcane_mosaic"], "segmentation_labels": ["mosaic_mottling"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Clear shot of the leaf mottling."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "5km", "report_count_threshold": "3", "outbreak_alert_message": "", "nearby_farm_advice": []},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""}
}

sugarcane_red_rot = {
    "id": "sugarcane_red_rot",
    "crop": sugarcane_mosaic["crop"],
    "disease": {
      "name": "Red Rot", "category": "Fungal", "pathogen_or_cause": ["Colletotrichum falcatum"], "affected_parts": ["Leaves", "Stalks"], "disease_stage": "All stages"
    },
    "symptoms": {
      "early_stage": ["Premature yellowing and wilting of upper leaves. Red patches with ash-colored centers on midribs."],
      "middle_stage": ["Cane loses firmness. Leaves wither."],
      "severe_stage": ["Internal stalk shows dark brown/red discoloration with white patches across the width. Sour alcoholic odor."],
      "visible_signs": ["Red/white banded pith inside the cane, sour smell."],
      "farmer_reported_signs": ["Inside of the cane is red with white spots", "Field smells like alcohol or vinegar", "Top leaves drying"]
    },
    "visual_identification": {
      "color_changes": ["Red", "White patches"], "spot_or_patch_shape": "Transverse white bands", "pattern": "Red pith with white bands", "location_on_plant": "Inside stalk, leaf midribs", "starts_from": "Internal stalk", "progression": "Wilting -> Internal rotting -> Death", "image_clues": ["Split cane showing red tissue with white cross-bands."]
    },
    "similar_diseases_or_issues": [
      {"name": "Wilt", "difference": "Wilt causes purple/red discoloration but lacks the distinct white horizontal patches and sour smell of red rot.", "confusion_risk": "High"}
    ],
    "favorable_conditions": {
      "weather": ["Warm, humid", "Heavy rains"], "temperature_range": "25-30C", "humidity_level": "High", "season": "Monsoon", "soil_conditions": ["Waterlogged"], "field_conditions": ["Debris present"], "irrigation_conditions": ["Stagnant water"]
    },
    "spread": {
      "spread_by": ["Infected setts", "Water runoff", "Soil"], "source_of_infection": ["Seed material", "Soil debris"], "survival_method": "In soil/debris", "spread_speed": "Fast in waterlogged fields", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "High", "description": "Internal rotting and wilting.", "field_indicator": "Sour smell in field.", "recommended_action": "Uproot and burn."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use certified disease-free setts.", "Hot water treatment (52C for 30 mins)."], "field_management": ["Improve drainage."], "irrigation_management": ["Avoid stagnation."], "soil_management": ["N/A"], "crop_rotation": ["Rotate for 3 years."], "sanitation": ["Uproot and burn infected plants."], "monitoring": ["Check midribs for lesions."]
    },
    "management": {
      "immediate_action": ["Remove and burn infected clumps."], "cultural_control": ["Drainage."], "organic_control": ["None effective for systemic rot."], "biological_control": ["N/A"], "chemical_control": [{"active_ingredient": "Thiophanate methyl", "product_type": "Fungicide", "dose": "0.2%", "application_method": "Sett dip", "spray_interval": "N/A", "pre_harvest_interval": "N/A", "safety_note": "Use before planting."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A devastating fungal disease known as the 'cancer of sugarcane', causing internal red rot.", "what_to_do_now": ["Uproot and burn the infected canes immediately."], "what_not_to_do": ["Don't use canes from this field for next planting.", "Don't ratoon the infected crop."], "when_to_call_expert": ["If you suspect red rot, confirm immediately."], "risk_warning": "Total crop failure is possible."
    },
    "model_support": {
      "classification_labels": ["sugarcane_red_rot"], "segmentation_labels": ["red_rot_pith"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Clear shot of a longitudinally split cane."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "5km", "report_count_threshold": "2", "outbreak_alert_message": "Red Rot spotted. Inspect your canes.", "nearby_farm_advice": ["Drain water."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""}
}

sunflower_leaf_scars = {
    "id": "sunflower_leaf_scars",
    "crop": {
      "common_name": "Sunflower", "english_name": "Sunflower", "scientific_name": "Helianthus annuus", "local_names": ["Surajmukhi"], "crop_category": "Oilseed"
    },
    "disease": {
      "name": "Leaf Scars (Generic / Abiotic)", "category": "Abiotic / Mechanical", "pathogen_or_cause": ["Insect feeding", "Hail", "Wind damage", "Mechanical injury"], "affected_parts": ["Leaves"], "disease_stage": "Any stage"
    },
    "symptoms": {
      "early_stage": ["Physical tearing or scratching on leaves."],
      "middle_stage": ["Edges of the torn tissue dry out and turn brown/tan."],
      "severe_stage": ["Large holes or tattered leaves."],
      "visible_signs": ["Dried brown edges around physical damage holes."],
      "farmer_reported_signs": ["Leaves look torn or eaten"]
    },
    "visual_identification": {
      "color_changes": ["Brown edges"], "spot_or_patch_shape": "Irregular holes or tears", "pattern": "Random", "location_on_plant": "Canopy", "starts_from": "Outer leaves", "progression": "Damage -> Drying of edges -> Stable scar", "image_clues": ["Look for physical holes with dry, healed brown edges."]
    },
    "similar_diseases_or_issues": [
      {"name": "Alternaria Leaf Spot", "difference": "Fungal spots have concentric rings, while scars are physical holes with simple brown dried edges.", "confusion_risk": "Low"}
    ],
    "favorable_conditions": {
      "weather": ["Hailstorms", "High winds"], "temperature_range": "N/A", "humidity_level": "N/A", "season": "Any", "soil_conditions": ["N/A"], "field_conditions": ["Presence of chewing insects"], "irrigation_conditions": ["N/A"]
    },
    "spread": {
      "spread_by": ["N/A"], "source_of_infection": ["N/A"], "survival_method": "N/A", "spread_speed": "N/A", "nearby_crop_risk": "Low"
    },
    "severity_levels": [
      {"level": "Low", "description": "Cosmetic damage.", "field_indicator": "A few torn leaves.", "recommended_action": "None."}
    ],
    "prevention": {
      "seed_or_planting_material": ["N/A"], "field_management": ["Control chewing pests if present."], "irrigation_management": ["N/A"], "soil_management": ["N/A"], "crop_rotation": ["N/A"], "sanitation": ["N/A"], "monitoring": ["N/A"]
    },
    "management": {
      "immediate_action": ["None required if abiotic."], "cultural_control": ["None."], "organic_control": ["None."], "biological_control": ["None."], "chemical_control": [], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "Physical damage to the leaf from weather or chewing insects that has healed over.", "what_to_do_now": ["Check if caterpillars or beetles are actively eating the plant."], "what_not_to_do": ["Don't spray fungicide; it is not a disease."], "when_to_call_expert": ["N/A"], "risk_warning": "No risk unless insect defoliation is extreme."
    },
    "model_support": {
      "classification_labels": ["sunflower_leaf_scars"], "segmentation_labels": ["healed_scar"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Clear shot of the hole/scar."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "N/A", "risk_radius": "0km", "report_count_threshold": "0", "outbreak_alert_message": "", "nearby_farm_advice": []},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": "Generic class for abiotic physical leaf damage."}
}

append_to_rag('Soyabean.txt', [soyabean_ferrugen, soyabean_powdery_mildew])
append_to_rag('Sugarcane.txt', [sugarcane_mosaic, sugarcane_red_rot])
append_to_rag('Sunflower.txt', [sunflower_leaf_scars])
print("Added Soyabean, Sugarcane, and Sunflower diseases.")
