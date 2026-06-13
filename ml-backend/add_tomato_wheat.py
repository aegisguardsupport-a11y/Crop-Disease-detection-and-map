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

tomato_spider_mite = {
    "id": "tomato_two-spotted_spider_mite",
    "crop": {
      "common_name": "Tomato", "english_name": "Tomato", "scientific_name": "Solanum lycopersicum", "local_names": ["Tamatar"], "crop_category": "Vegetable"
    },
    "disease": {
      "name": "Two-Spotted Spider Mite", "category": "Pest", "pathogen_or_cause": ["Tetranychus urticae"], "affected_parts": ["Leaves"], "disease_stage": "Any stage"
    },
    "symptoms": {
      "early_stage": ["Mottled, speckled, or 'stippled' appearance on upper leaf surfaces (tiny white/yellow dots)."],
      "middle_stage": ["Leaves turn yellow and develop a crusty tan/yellow texture underneath."],
      "severe_stage": ["Fine, silk-like webbing covers leaves. Leaves dry up and drop. Plant may die."],
      "visible_signs": ["Stippling on leaves, fine webbing, tiny moving specks."],
      "farmer_reported_signs": ["Leaves look dusty and yellow", "Webs on the plant like a spider web"]
    },
    "visual_identification": {
      "color_changes": ["Yellowing", "Tan"], "spot_or_patch_shape": "Tiny pinprick stippling", "pattern": "Speckled all over leaf", "location_on_plant": "Underside of leaves primarily", "starts_from": "Lower or edge leaves", "progression": "Stippling -> Webbing -> Yellowing -> Drying", "image_clues": ["Look for fine webbing and yellow stippling on leaves."]
    },
    "similar_diseases_or_issues": [
      {"name": "Nutrient deficiency", "difference": "Deficiencies cause solid yellowing, while spider mites cause distinctly speckled yellowing (stippling).", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Hot, dry"], "temperature_range": "25-35C", "humidity_level": "<50%", "season": "Summer", "soil_conditions": ["Dry"], "field_conditions": ["Dusty roadsides"], "irrigation_conditions": ["Drought stress"]
    },
    "spread": {
      "spread_by": ["Wind", "Workers' clothing"], "source_of_infection": ["Weeds", "Nearby infested crops"], "survival_method": "Overwinter in soil/weeds", "spread_speed": "Very Fast in hot weather", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "High", "description": "Webbing present.", "field_indicator": "Leaves drying.", "recommended_action": "Apply miticide immediately."}
    ],
    "prevention": {
      "seed_or_planting_material": ["N/A"], "field_management": ["Control weeds near field."], "irrigation_management": ["Keep plants well-watered to reduce stress."], "soil_management": ["N/A"], "crop_rotation": ["N/A"], "sanitation": ["Remove heavily infested plants."], "monitoring": ["Shake leaves over white paper to see mites."]
    },
    "management": {
      "immediate_action": ["Spray horticultural oil or miticide."], "cultural_control": ["Reduce dust (spray water on dirt roads)."], "organic_control": ["Neem oil or insecticidal soap (ensure underside coverage)."], "biological_control": ["Release predatory mites (Phytoseiulus persimilis)."], "chemical_control": [{"active_ingredient": "Abamectin", "product_type": "Miticide", "dose": "1mL/L", "application_method": "Spray", "spray_interval": "10 days", "pre_harvest_interval": "7 days", "safety_note": "Ensure thorough coverage of leaf undersides."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "Tiny sap-sucking pests that thrive in hot, dry weather, causing leaves to turn yellow and webbed.", "what_to_do_now": ["Spray an approved miticide or neem oil, targeting the UNDERSIDE of the leaves."], "what_not_to_do": ["Don't let the plants suffer from drought."], "when_to_call_expert": ["If miticide doesn't work (they develop resistance fast)."], "risk_warning": "Can kill the plant if webs cover it completely."
    },
    "model_support": {
      "classification_labels": ["tomato_two-spotted_spider_mite"], "segmentation_labels": ["stippling", "spider_mite_webbing"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Close-up of the stippling or webbing."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "5km", "report_count_threshold": "3", "outbreak_alert_message": "Spider mites active in hot weather.", "nearby_farm_advice": ["Monitor undersides of leaves."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""}
}

wheat_septoria = {
    "id": "wheat_septoria",
    "crop": {
      "common_name": "Wheat", "english_name": "Wheat", "scientific_name": "Triticum aestivum", "local_names": ["Gehu"], "crop_category": "Cereal"
    },
    "disease": {
      "name": "Septoria Tritici Blotch", "category": "Fungal", "pathogen_or_cause": ["Zymoseptoria tritici"], "affected_parts": ["Leaves"], "disease_stage": "Tillering to Heading"
    },
    "symptoms": {
      "early_stage": ["Small, chlorotic (yellow) spots on lower leaves."],
      "middle_stage": ["Spots expand into irregular, light tan to reddish-brown lesions, often rectangular/elongated, restricted by veins."],
      "severe_stage": ["Tiny black fruiting bodies (pycnidia) appear inside the dead tissue like black pepper grains. Leaves die prematurely."],
      "visible_signs": ["Tan rectangular lesions with tiny black dots inside."],
      "farmer_reported_signs": ["Brown patches on leaves", "Tiny black specks in the brown patches"]
    },
    "visual_identification": {
      "color_changes": ["Tan", "Reddish-brown", "Yellow"], "spot_or_patch_shape": "Elongated, rectangular", "pattern": "Restricted by leaf veins", "location_on_plant": "Lower leaves first", "starts_from": "Lower canopy", "progression": "Spots -> Necrosis -> Pycnidia formation -> Death", "image_clues": ["Look for the tiny black pepper-like dots inside the brown lesions."]
    },
    "similar_diseases_or_issues": [
      {"name": "Tan Spot", "difference": "Tan spot lacks the prominent tiny black pycnidia found in Septoria lesions.", "confusion_risk": "High"}
    ],
    "favorable_conditions": {
      "weather": ["Cool, wet", "Frequent rain"], "temperature_range": "15-20C", "humidity_level": ">85%", "season": "Spring", "soil_conditions": ["N/A"], "field_conditions": ["Dense canopy"], "irrigation_conditions": ["Overhead irrigation"]
    },
    "spread": {
      "spread_by": ["Rain splash", "Wind"], "source_of_infection": ["Infected wheat stubble"], "survival_method": "In stubble", "spread_speed": "Moderate", "nearby_crop_risk": "Medium"
    },
    "severity_levels": [
      {"level": "Medium", "description": "Lesions reaching upper leaves (flag leaf).", "field_indicator": "Disease moving up canopy.", "recommended_action": "Apply foliar fungicide."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use resistant varieties."], "field_management": ["Delay drilling/planting if in high-risk area."], "irrigation_management": ["N/A"], "soil_management": ["Bury or manage crop stubble."], "crop_rotation": ["Rotate with non-cereals for 1 year."], "sanitation": ["N/A"], "monitoring": ["Scout lower leaves during spring."]
    },
    "management": {
      "immediate_action": ["Spray fungicide before it hits the flag leaf."], "cultural_control": ["Stubble management."], "organic_control": ["None highly effective."], "biological_control": ["N/A"], "chemical_control": [{"active_ingredient": "Propiconazole + Azoxystrobin", "product_type": "Fungicide", "dose": "1mL/L", "application_method": "Spray", "spray_interval": "14 days", "pre_harvest_interval": "30 days", "safety_note": "Rotate fungicide classes."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A fungus that causes brown rectangular spots with black specks on leaves, reducing yield if it reaches the top leaves.", "what_to_do_now": ["Apply a recommended fungicide if the weather is rainy."], "what_not_to_do": ["Don't ignore symptoms moving up the plant."], "when_to_call_expert": ["To distinguish from Tan Spot."], "risk_warning": "Protecting the flag leaf is critical for yield."
    },
    "model_support": {
      "classification_labels": ["wheat_septoria"], "segmentation_labels": ["septoria_lesion", "pycnidia"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Macro shot showing the black pycnidia dots."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "20km", "report_count_threshold": "3", "outbreak_alert_message": "Septoria risk is high due to rain.", "nearby_farm_advice": ["Scout fields now."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""}
}

wheat_stripe_rust = {
    "id": "wheat_stripe_rust",
    "crop": wheat_septoria["crop"],
    "disease": {
      "name": "Stripe Rust (Yellow Rust)", "category": "Fungal", "pathogen_or_cause": ["Puccinia striiformis f. sp. tritici"], "affected_parts": ["Leaves", "Glumes"], "disease_stage": "Any stage"
    },
    "symptoms": {
      "early_stage": ["Small, bright yellow to orange-yellow powdery pustules on leaves."],
      "middle_stage": ["Pustules align to form narrow, linear stripes parallel to leaf veins."],
      "severe_stage": ["Leaves turn yellow, brown, and dry out. Stunted growth, shriveled grains."],
      "visible_signs": ["Yellow/orange powdery stripes on leaves."],
      "farmer_reported_signs": ["Yellow powder forming lines on the leaves", "Yellow dust gets on clothes when walking in field"]
    },
    "visual_identification": {
      "color_changes": ["Yellow-orange"], "spot_or_patch_shape": "Linear stripes", "pattern": "Parallel to veins", "location_on_plant": "Leaves primarily", "starts_from": "Upper or lower leaves", "progression": "Pustules -> Stripes -> Necrosis", "image_clues": ["Look for bright yellow powder arranged in distinct stripes/lines."]
    },
    "similar_diseases_or_issues": [
      {"name": "Leaf Rust (Brown Rust)", "difference": "Leaf rust pustules are randomly scattered and darker orange/brown, while stripe rust forms distinct parallel yellow stripes.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Cool, moist", "Dewy nights"], "temperature_range": "10-20C", "humidity_level": "High", "season": "Spring", "soil_conditions": ["N/A"], "field_conditions": ["N/A"], "irrigation_conditions": ["Prolonged leaf wetness"]
    },
    "spread": {
      "spread_by": ["Wind (long distances)"], "source_of_infection": ["Wind-blown spores", "Volunteer wheat"], "survival_method": "Green bridge (living plants)", "spread_speed": "Very Fast", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "High", "description": "Stripe rust pustules spreading rapidly.", "field_indicator": "Yellow dust in field.", "recommended_action": "Spray systemic fungicide immediately."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use resistant varieties (check latest ratings)."], "field_management": ["Destroy volunteer wheat (green bridge) before planting."], "irrigation_management": ["N/A"], "soil_management": ["Avoid excess nitrogen."], "crop_rotation": ["Rotate with non-hosts."], "sanitation": ["N/A"], "monitoring": ["Scout early in spring."]
    },
    "management": {
      "immediate_action": ["Spray fungicide at first sign."], "cultural_control": ["None once infected."], "organic_control": ["Not highly effective."], "biological_control": ["N/A"], "chemical_control": [{"active_ingredient": "Tebuconazole", "product_type": "Fungicide", "dose": "1mL/L", "application_method": "Spray", "spray_interval": "15 days", "pre_harvest_interval": "30 days", "safety_note": "Apply before it reaches flag leaf."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A highly destructive fungus causing yellow powdery stripes on leaves.", "what_to_do_now": ["Spray an approved triazole fungicide immediately."], "what_not_to_do": ["Don't delay spraying; it spreads extremely fast."], "when_to_call_expert": ["If variety was supposed to be resistant but shows infection (new strain possible)."], "risk_warning": "Can decimate yields if untreated."
    },
    "model_support": {
      "classification_labels": ["wheat_stripe_rust"], "segmentation_labels": ["yellow_stripe_pustule"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Clear shot of the parallel yellow stripes."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "State", "risk_radius": "50km", "report_count_threshold": "1", "outbreak_alert_message": "Stripe rust detected in the region.", "nearby_farm_advice": ["Scout and spray."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""}
}

append_to_rag('Tomato.txt', [tomato_spider_mite])
append_to_rag('Wheat.txt', [wheat_septoria, wheat_stripe_rust])
print("Added Tomato and Wheat diseases.")
