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

cotton_fusarium_wilt = {
    "id": "cotton_fussarium_wilt",
    "crop": {
      "common_name": "Cotton", "english_name": "Cotton", "scientific_name": "Gossypium hirsutum", "local_names": ["Kapas"], "crop_category": "Fiber"
    },
    "disease": {
      "name": "Fusarium Wilt", "category": "Fungal", "pathogen_or_cause": ["Fusarium oxysporum f. sp. vasinfectum"], "affected_parts": ["Roots", "Vascular system", "Leaves"], "disease_stage": "Seedling to Mature"
    },
    "symptoms": {
      "early_stage": ["Poor germination, seedlings wilt rapidly."],
      "middle_stage": ["Lower leaves show yellowing (chlorosis) or browning at margins. Sudden wilting during heat."],
      "severe_stage": ["Continuous brown discoloration in the internal vascular tissue of stem/root. Stunting and death."],
      "visible_signs": ["Brown ring inside cut stems, wilting."],
      "farmer_reported_signs": ["Plants wilt in hot sun", "Brown ring inside the stem", "Lower leaves drying"]
    },
    "visual_identification": {
      "color_changes": ["Yellowing leaves", "Brown vascular ring"], "spot_or_patch_shape": "None on leaves (systemic)", "pattern": "Vascular browning", "location_on_plant": "Systemic", "starts_from": "Roots", "progression": "Root infection -> Vascular blockage -> Wilting -> Death", "image_clues": ["Cut stem showing dark brown ring inside."]
    },
    "similar_diseases_or_issues": [
      {"name": "Verticillium Wilt", "difference": "Verticillium causes mottled yellowing between veins, often on cooler days, while Fusarium browning in the stem is continuous rather than streaky.", "confusion_risk": "High"}
    ],
    "favorable_conditions": {
      "weather": ["Warm, dry periods followed by wet"], "temperature_range": "25-30C", "humidity_level": "Variable", "season": "Summer", "soil_conditions": ["Acidic, sandy", "Presence of root-knot nematodes"], "field_conditions": ["Infested soil"], "irrigation_conditions": ["Water stress"]
    },
    "spread": {
      "spread_by": ["Soil movement", "Water", "Farm tools"], "source_of_infection": ["Soil", "Seed"], "survival_method": "Chlamydospores in soil for years", "spread_speed": "Moderate", "nearby_crop_risk": "Low (host specific)"
    },
    "severity_levels": [
      {"level": "High", "description": "Severe wilting.", "field_indicator": "Brown vascular rings.", "recommended_action": "Uproot and destroy."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Use resistant varieties.", "Carbendazim seed treatment."], "field_management": ["Manage nematode populations."], "irrigation_management": ["Consistent watering."], "soil_management": ["Avoid excess nitrogen."], "crop_rotation": ["Rotate non-hosts for 3-4 years."], "sanitation": ["Destroy crop debris."], "monitoring": ["Scout for wilting."]
    },
    "management": {
      "immediate_action": ["Remove infected plants."], "cultural_control": ["Manage root-knot nematodes."], "organic_control": ["Trichoderma viride soil application."], "biological_control": ["Trichoderma sp."], "chemical_control": [{"active_ingredient": "Carbendazim", "product_type": "Fungicide", "dose": "2g/kg", "application_method": "Seed Treatment", "spray_interval": "N/A", "pre_harvest_interval": "N/A", "safety_note": "Handle treated seeds carefully."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A soil fungus that blocks the plant's water pipes, causing it to wilt and die.", "what_to_do_now": ["Apply Trichoderma to soil if early."], "what_not_to_do": ["Don't move infested soil."], "when_to_call_expert": ["To confirm via stem cutting."], "risk_warning": "Very hard to eradicate from soil once established."
    },
    "model_support": {
      "classification_labels": ["cotton_fussarium_wilt"], "segmentation_labels": ["wilted_leaf", "vascular_browning"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["Similar to Verticillium."], "image_quality_requirements": ["Cross section of stem."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "Field", "risk_radius": "0km", "report_count_threshold": "1", "outbreak_alert_message": "Wilt detected.", "nearby_farm_advice": ["Check roots."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

groundnut_dead_leaf = {
    "id": "groundnut_dead_leaf",
    "crop": {
      "common_name": "Groundnut", "english_name": "Peanut", "scientific_name": "Arachis hypogaea", "local_names": ["Moongphali"], "crop_category": "Oilseed"
    },
    "disease": {
      "name": "Dead Leaf (Generic)", "category": "Abiotic / Senescence", "pathogen_or_cause": ["Natural aging", "Water stress", "Nutrient deficiency"], "affected_parts": ["Leaves"], "disease_stage": "Late stage"
    },
    "symptoms": {
      "early_stage": ["Overall yellowing or browning of older leaves."],
      "middle_stage": ["Leaves turn completely brown and dry."],
      "severe_stage": ["Leaves fall off naturally or remain attached if rapidly desiccated."],
      "visible_signs": ["Crispy brown dead leaves at the base."],
      "farmer_reported_signs": ["Bottom leaves drying up and dying"]
    },
    "visual_identification": {
      "color_changes": ["Brown", "Yellow"], "spot_or_patch_shape": "Whole leaf", "pattern": "Uniform drying", "location_on_plant": "Lower canopy", "starts_from": "Older leaves", "progression": "Yellowing -> Drying -> Dropping", "image_clues": ["Uniformly brown dry leaf with no distinct spots or fuzz."]
    },
    "similar_diseases_or_issues": [
      {"name": "Leaf Spot (Tikka)", "difference": "Tikka has distinct dark spots with yellow halos, while dead leaf is generally uniform browning without specific distinct spots.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Hot, dry"], "temperature_range": ">35C", "humidity_level": "<50%", "season": "Summer", "soil_conditions": ["Dry"], "field_conditions": ["Water stress"], "irrigation_conditions": ["Drought"]
    },
    "spread": {
      "spread_by": ["N/A"], "source_of_infection": ["N/A"], "survival_method": "N/A", "spread_speed": "N/A", "nearby_crop_risk": "Low"
    },
    "severity_levels": [
      {"level": "Low", "description": "Natural senescence.", "field_indicator": "Only oldest leaves.", "recommended_action": "Ensure adequate watering."}
    ],
    "prevention": {
      "seed_or_planting_material": ["N/A"], "field_management": ["Proper nutrition."], "irrigation_management": ["Consistent watering."], "soil_management": ["Mulching."], "crop_rotation": ["N/A"], "sanitation": ["N/A"], "monitoring": ["Monitor soil moisture."]
    },
    "management": {
      "immediate_action": ["Water the crop if dry."], "cultural_control": ["None."], "organic_control": ["None."], "biological_control": ["None."], "chemical_control": [], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "Leaves dying due to old age or lack of water/nutrients.", "what_to_do_now": ["Check soil moisture."], "what_not_to_do": ["Don't spray fungicides unnecessarily."], "when_to_call_expert": ["If young leaves are dying."], "risk_warning": "No major risk unless widespread."
    },
    "model_support": {
      "classification_labels": ["groundnut_dead_leaf"], "segmentation_labels": ["dead_leaf_tissue"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Clear shot of the leaf."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "N/A", "risk_radius": "0km", "report_count_threshold": "0", "outbreak_alert_message": "", "nearby_farm_advice": []},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

groundnut_diseased_leaf = {
    "id": "groundnut_diseased_leaf",
    "crop": groundnut_dead_leaf["crop"],
    "disease": {
      "name": "Diseased Leaf (Generic)", "category": "Fungal / Unknown", "pathogen_or_cause": ["Fungal complex (Alternaria, Cercospora, etc.)"], "affected_parts": ["Leaves"], "disease_stage": "Any stage"
    },
    "symptoms": {
      "early_stage": ["Unspecified spots or blighting on the leaf."],
      "middle_stage": ["Spots expand, causing tissue necrosis and yellowing."],
      "severe_stage": ["Leaf drop and plant weakening."],
      "visible_signs": ["Spots, blights, or necrosis on leaves."],
      "farmer_reported_signs": ["Leaves looking sick or spotted"]
    },
    "visual_identification": {
      "color_changes": ["Yellow", "Brown", "Black"], "spot_or_patch_shape": "Variable spots", "pattern": "Variable", "location_on_plant": "Leaves", "starts_from": "Anywhere", "progression": "Spotting -> Blighting", "image_clues": ["Leaf with unspecified lesions."]
    },
    "similar_diseases_or_issues": [
      {"name": "Tikka / Rust", "difference": "This is a generic class for undiagnosed leaf spots.", "confusion_risk": "High"}
    ],
    "favorable_conditions": {
      "weather": ["Warm, humid"], "temperature_range": "20-30C", "humidity_level": ">80%", "season": "Monsoon", "soil_conditions": ["Variable"], "field_conditions": ["Dense planting"], "irrigation_conditions": ["Overhead"]
    },
    "spread": {
      "spread_by": ["Wind", "Water"], "source_of_infection": ["Debris"], "survival_method": "Crop residue", "spread_speed": "Variable", "nearby_crop_risk": "Medium"
    },
    "severity_levels": [
      {"level": "Medium", "description": "Spotting on leaves.", "field_indicator": "10% foliage.", "recommended_action": "Apply broad-spectrum fungicide."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Healthy seeds."], "field_management": ["Weed control."], "irrigation_management": ["Drip irrigation."], "soil_management": ["Good drainage."], "crop_rotation": ["Rotate non-legumes."], "sanitation": ["Destroy debris."], "monitoring": ["Scout fields."]
    },
    "management": {
      "immediate_action": ["Remove worst affected leaves."], "cultural_control": ["Sanitation."], "organic_control": ["Neem spray."], "biological_control": ["Trichoderma."], "chemical_control": [{"active_ingredient": "Mancozeb", "product_type": "Broad-spectrum Fungicide", "dose": "2g/L", "application_method": "Spray", "spray_interval": "10 days", "pre_harvest_interval": "10 days", "safety_note": "Apply as protective."}], "expert_recommendation_required": True
    },
    "farmer_advice": {
      "simple_explanation": "A generic leaf spot disease requiring broad-spectrum treatment.", "what_to_do_now": ["Spray Mancozeb or Chlorothalonil."], "what_not_to_do": ["Don't use overhead sprinklers."], "when_to_call_expert": ["To identify specific pathogen if it doesn't respond to spray."], "risk_warning": "Yield loss if unchecked."
    },
    "model_support": {
      "classification_labels": ["groundnut_diseased_leaf"], "segmentation_labels": ["disease_lesion"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["Always, for exact diagnosis."], "image_quality_requirements": ["Clear photo of spots."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "5km", "report_count_threshold": "5", "outbreak_alert_message": "Foliar disease spread.", "nearby_farm_advice": ["Spray broad-spectrum fungicide."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "Medium", "notes": "Generic class for unclassified leaf spots."},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

rice_bacterial_blight = {
    "id": "rice_bacterialblight",
    "crop": {
      "common_name": "Rice", "english_name": "Rice", "scientific_name": "Oryza sativa", "local_names": ["Dhan"], "crop_category": "Cereal"
    },
    "disease": {
      "name": "Bacterial Blight", "category": "Bacterial", "pathogen_or_cause": ["Xanthomonas oryzae pv. oryzae"], "affected_parts": ["Leaves", "Seedlings"], "disease_stage": "Seedling to Mature"
    },
    "symptoms": {
      "early_stage": ["Water-soaked yellowish stripes on leaf blades, starting at tips."],
      "middle_stage": ["Lesions expand with wavy margin, turning yellowish-white. Ooze appears in morning."],
      "severe_stage": ["Leaves dry, curl, and turn straw-colored. 'Kresek' (seedling wilt) causes death of whole seedling."],
      "visible_signs": ["Yellow wavy stripes, morning bacterial ooze drops."],
      "farmer_reported_signs": ["Leaves turning yellow and drying from the tips", "Seedlings wilting and dying"]
    },
    "visual_identification": {
      "color_changes": ["Yellowish-white", "Straw colored"], "spot_or_patch_shape": "Long wavy stripes", "pattern": "Following leaf veins from tip", "location_on_plant": "Leaves", "starts_from": "Leaf tips and margins", "progression": "Tip -> Downwards -> Leaf death", "image_clues": ["Look for yellow wavy stripes with dried tips."]
    },
    "similar_diseases_or_issues": [
      {"name": "Leaf streak", "difference": "Streak forms narrow translucent streaks between veins, not large wavy stripes from tips.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Warm, humid", "Typhoon or heavy rain"], "temperature_range": "25-34C", "humidity_level": ">70%", "season": "Monsoon", "soil_conditions": ["Waterlogged"], "field_conditions": ["Excess nitrogen", "Dense planting"], "irrigation_conditions": ["Stagnant water"]
    },
    "spread": {
      "spread_by": ["Wind-driven rain", "Irrigation water", "Contact"], "source_of_infection": ["Weeds", "Stubble"], "survival_method": "In weeds and crop debris", "spread_speed": "Very Fast", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "High", "description": "Kresek wilt or severe leaf drying.", "field_indicator": "Straw-colored fields.", "recommended_action": "Drain water, stop nitrogen."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Resistant varieties (e.g. IR64)."], "field_management": ["Optimal spacing."], "irrigation_management": ["Drain field periodically."], "soil_management": ["Avoid excess N."], "crop_rotation": ["Rotate to non-host."], "sanitation": ["Remove stubble and weeds."], "monitoring": ["Check tips after storms."]
    },
    "management": {
      "immediate_action": ["Drain excess water.", "Stop urea application."], "cultural_control": ["Field drainage."], "organic_control": ["None highly effective."], "biological_control": ["Pseudomonas fluorescens."], "chemical_control": [{"active_ingredient": "Streptocycline + Copper Oxychloride", "product_type": "Bactericide", "dose": "0.1g + 2g/L", "application_method": "Spray", "spray_interval": "10 days", "pre_harvest_interval": "15 days", "safety_note": "Spray evenly."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A bacterial disease causing yellow wavy stripes and drying of rice leaves.", "what_to_do_now": ["Drain the water from the field.", "Do NOT apply urea."], "what_not_to_do": ["Don't keep water stagnant.", "Don't over-fertilize."], "when_to_call_expert": ["If kresek occurs early."], "risk_warning": "Can drastically reduce yield."
    },
    "model_support": {
      "classification_labels": ["rice_bacterialblight"], "segmentation_labels": ["wavy_yellow_stripe"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["None"], "image_quality_requirements": ["Clear view of leaf tip."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "10km", "report_count_threshold": "5", "outbreak_alert_message": "Bacterial Blight alert after heavy rains.", "nearby_farm_advice": ["Drain fields, avoid urea."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

rice_tungro = {
    "id": "rice_tungro",
    "crop": rice_bacterial_blight["crop"],
    "disease": {
      "name": "Tungro", "category": "Viral", "pathogen_or_cause": ["Rice tungro bacilliform virus (RTBV)", "Rice tungro spherical virus (RTSV)"], "affected_parts": ["Leaves", "Whole plant"], "disease_stage": "Vegetative to Heading"
    },
    "symptoms": {
      "early_stage": ["Discoloration of leaves starting from tip to downward (yellow/orange)."],
      "middle_stage": ["Stunted growth, reduced tillering, rust-colored spots on older leaves."],
      "severe_stage": ["Delayed flowering, small panicles, empty grains."],
      "visible_signs": ["Stunted yellow/orange plants, presence of Green Leafhoppers."],
      "farmer_reported_signs": ["Plants are stunted and turn yellow-orange", "A lot of green insects in the field"]
    },
    "visual_identification": {
      "color_changes": ["Yellow", "Orange-yellow"], "spot_or_patch_shape": "Whole leaf discoloration", "pattern": "Interveinal stripes or mottling", "location_on_plant": "Systemic", "starts_from": "Leaf tips", "progression": "Discoloration -> Stunting -> Sterile panicles", "image_clues": ["Look for orange-yellow stunted plants."]
    },
    "similar_diseases_or_issues": [
      {"name": "Nitrogen deficiency", "difference": "Nitrogen deficiency causes uniform pale yellowing without the intense orange hue or severe stunting of tungro.", "confusion_risk": "Medium"}
    ],
    "favorable_conditions": {
      "weather": ["Warm"], "temperature_range": "25-30C", "humidity_level": "Variable", "season": "Any", "soil_conditions": ["N/A"], "field_conditions": ["Presence of Green Leafhopper vectors"], "irrigation_conditions": ["N/A"]
    },
    "spread": {
      "spread_by": ["Green Leafhopper (GLH)"], "source_of_infection": ["Infected weeds", "Volunteer rice"], "survival_method": "In alternative hosts", "spread_speed": "Fast if GLH is present", "nearby_crop_risk": "High"
    },
    "severity_levels": [
      {"level": "High", "description": "Severe stunting and orange leaves.", "field_indicator": "High GLH population.", "recommended_action": "Spray insecticide against GLH."}
    ],
    "prevention": {
      "seed_or_planting_material": ["Resistant varieties."], "field_management": ["Synchronous planting.", "Destroy alternative weed hosts."], "irrigation_management": ["N/A"], "soil_management": ["Avoid excess nitrogen."], "crop_rotation": ["N/A"], "sanitation": ["Plow under infected stubble."], "monitoring": ["Scout for Green Leafhoppers."]
    },
    "management": {
      "immediate_action": ["Control GLH vectors immediately."], "cultural_control": ["Remove symptomatic plants early."], "organic_control": ["Neem oil to repel insects."], "biological_control": ["Spiders and natural GLH enemies."], "chemical_control": [{"active_ingredient": "Imidacloprid", "product_type": "Insecticide", "dose": "0.5mL/L", "application_method": "Spray", "spray_interval": "14 days", "pre_harvest_interval": "15 days", "safety_note": "Target vectors."}], "expert_recommendation_required": False
    },
    "farmer_advice": {
      "simple_explanation": "A virus spread by green leafhoppers causing yellow/orange stunted plants.", "what_to_do_now": ["Spray insecticide to kill the green leafhoppers."], "what_not_to_do": ["Don't ignore the presence of green insects on the leaves."], "when_to_call_expert": ["To confirm tungro vs nutrient deficiency via iodine test."], "risk_warning": "Can cause massive yield loss if young plants are infected."
    },
    "model_support": {
      "classification_labels": ["rice_tungro"], "segmentation_labels": ["orange_discolored_leaf"], "confidence_threshold": {"low": "0.5", "medium": "0.7", "high": "0.9"}, "send_to_expert_if": ["Nutrient deficiency is suspected."], "image_quality_requirements": ["Clear shot of the colored leaves and whole plant structure."]
    },
    "rag_chunks": [], "geo_outbreak_data": {"location_level": "District", "risk_radius": "10km", "report_count_threshold": "4", "outbreak_alert_message": "Tungro alert. Spray against GLH.", "nearby_farm_advice": ["Monitor GLH."]},
    "source_metadata": {"source_title": "AgriTech", "source_url": "https://agritech.tnau.ac.in", "source_type": "Guide", "author_or_organization": "TNAU", "published_year": "2023", "region": "India", "language": "English", "last_verified": "2024", "trust_level": "High", "notes": ""},
    "versioning": {"created_at": "2024-10-27T00:00:00Z", "updated_at": "2024-10-27T00:00:00Z", "reviewed_by": "System", "status": "Approved"}
}

append_to_rag('Cotton.txt', [cotton_fusarium_wilt])
append_to_rag('Groundnut.txt', [groundnut_dead_leaf, groundnut_diseased_leaf])
append_to_rag('Rice.txt', [rice_bacterial_blight, rice_tungro])
print("Added Cotton, Groundnut, and Rice diseases.")
