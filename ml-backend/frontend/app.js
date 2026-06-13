/* ==========================================================================
   MOCK SCENARIO DATA DEFINITIONS
   ========================================================================== */

const SCENARIOS = {
    tomato_late_blight: {
        decision: 'high_confidence',
        confidence: 0.924,
        predictions: [
            { label: 'Tomato::Late Blight', confidence: 0.924, crop: 'Tomato', disease: 'Late Blight' },
            { label: 'Tomato::Septoria Leaf Spot', confidence: 0.051, crop: 'Tomato', disease: 'Septoria Leaf Spot' },
            { label: 'Tomato::Healthy', confidence: 0.025, crop: 'Tomato', disease: 'Healthy' }
        ],
        crop_router: [
            { crop: 'Tomato', confidence: 0.982 },
            { crop: 'Sugarcane', confidence: 0.012 },
            { crop: 'Rice', confidence: 0.006 }
        ],
        clip: [
            { crop: 'Tomato', similarity: 0.915 },
            { crop: 'Sugarcane', similarity: 0.042 },
            { crop: 'Rice', similarity: 0.021 }
        ],
        validation: {
            quality: { ok: true, score: 0.94, blur: 12, brightness: 142, contrast: 82, resolution: [4032, 3024], failures: [] },
            segmentation: { detected: true, confidence: 0.96, num_detections: 1, ratio: 0.28 },
            area: { ok: true, score: 0.98, ratio: 0.28, failure: null }
        },
        advisory: {
            summary: "Late blight identified. This is a highly destructive fungal disease affecting tomato crops during cool, wet weather.",
            symptoms: [
                "Dark, water-soaked spots on leaves that expand rapidly.",
                "White, fuzzy fungal growth on the underside of infected leaves in humid weather.",
                "Brown, leathery lesions developing on stalks, leading to vine collapse."
            ],
            organic: [
                "Prune infected lower foliage immediately and discard away from fields.",
                "Apply copper-based organic sprays or biological controls (Bacillus subtilis).",
                "Mulch heavily around base of tomato plants to prevent spore splash-back from soil."
            ],
            chemical: [
                "Apply chlorothalonil, mancozeb, or metalaxyl-based sprays at first sight of outbreak.",
                "Rotate chemical classes weekly to prevent fungal pathotypes from building resistance."
            ],
            prevention: [
                "Implement 3-year crop rotation schedules (avoid nightshade family crops).",
                "Utilize drip irrigation rather than overhead watering to keep foliage dry.",
                "Space crops appropriately to promote ventilation and solar disinfection."
            ],
            expert: "Immediate action required. Late blight spreads via airborne spores and can wipe out fields in 3-5 days.",
            citations: [
                { source: "CPL_Tomato_Manual.txt (p. 42)", text: "Late blight (Phytophthora infestans) is prioritized for control due to rapid sporulation under relative humidity > 90% and temperature between 15-22°C.", similarity: 0.88 },
                { source: "AgriExtension_Leaflet_10.txt (p. 2)", text: "Drip lines are highly recommended over sprinklers to decrease water leaf-contact duration, keeping moisture levels below pathogen germination thresholds.", similarity: 0.84 }
            ]
        },
        latency: { quality_ms: 42, segmentation_ms: 124, extract_ms: 18, classification_ms: 224, explain_ms: 642, advisory_ms: 1120, total_ms: 2170 },
        leaf_color: '#4d8054',
        spot_color: '#5c4538',
        spots: [
            { x: 120, y: 110, r: 24, blur: 8 },
            { x: 160, y: 150, r: 18, blur: 6 },
            { x: 100, y: 180, r: 15, blur: 4 }
        ],
        heatmap_spots: [
            { x: 120, y: 110, r: 40, intens: 1.0 },
            { x: 160, y: 150, r: 35, intens: 0.8 },
            { x: 100, y: 180, r: 30, intens: 0.7 }
        ]
    },
    sugarcane_rust: {
        decision: 'expert_review',
        confidence: 0.684,
        predictions: [
            { label: 'Sugarcane::Rust', confidence: 0.684, crop: 'Sugarcane', disease: 'Rust' },
            { label: 'Sugarcane::Healthy', confidence: 0.212, crop: 'Sugarcane', disease: 'Healthy' },
            { label: 'Maize::Common Rust', confidence: 0.104, crop: 'Maize', disease: 'Common Rust' }
        ],
        crop_router: [
            { crop: 'Sugarcane', confidence: 0.742 },
            { crop: 'Maize', confidence: 0.184 },
            { crop: 'Wheat', confidence: 0.074 }
        ],
        clip: [
            { crop: 'Sugarcane', similarity: 0.685 },
            { crop: 'Maize', similarity: 0.512 },
            { crop: 'Tomato', similarity: 0.104 }
        ],
        validation: {
            quality: { ok: true, score: 0.88, blur: 24, brightness: 172, contrast: 74, resolution: [3264, 2448], failures: [] },
            segmentation: { detected: true, confidence: 0.84, num_detections: 2, ratio: 0.14 },
            area: { ok: true, score: 0.78, ratio: 0.14, failure: 'suboptimal_area' }
        },
        advisory: {
            summary: "Sugarcane Rust detected with medium confidence. Diverted to Expert Review for confirmation due to partial visual overlaps with Maize Rust.",
            symptoms: [
                "Elongated, orange-brown pustules on both leaf surfaces.",
                "Pustules rupture releasing powdery rust spores (urediniospores).",
                "Leaves turning prematurely yellow and dry in severe infection zones."
            ],
            organic: [
                "Plant resistant sugarcane cultivars (Co 86032 / Co 99004).",
                "Remove and bury infected crops during initial growth phases.",
                "Apply organic bio-fungicides based on Pseudomonas fluorescens."
            ],
            chemical: [
                "Apply propiconazole or triadimefon at first sign of pustule emergence.",
                "Chemical treatments are recommended only under high economic crop density."
            ],
            prevention: [
                "Ensure balanced nitrogenous fertilizations; excess nitrogen intensifies canopy thickness, fostering rust spores.",
                "Maintain weed control to reduce microclimatic humidity levels."
            ],
            expert: "Sent to regional office expert queue. Visual structure resembles Maize Common Rust. Please check border crop contamination.",
            citations: [
                { source: "CPL_Sugarcane_Manual.txt (p. 18)", text: "Puccinia melanocephala (Brown Rust) displays linear pustules measuring 2-10 mm. Easily confused with Puccinia polysora in immature states.", similarity: 0.79 }
            ]
        },
        latency: { quality_ms: 45, segmentation_ms: 132, extract_ms: 15, classification_ms: 212, explain_ms: 590, advisory_ms: 980, total_ms: 1974 },
        leaf_color: '#71854c',
        spot_color: '#b0652a',
        spots: [
            { x: 110, y: 80, r: 12, blur: 3 },
            { x: 130, y: 130, r: 10, blur: 2 },
            { x: 140, y: 180, r: 14, blur: 4 },
            { x: 160, y: 220, r: 8, blur: 2 }
        ],
        heatmap_spots: [
            { x: 110, y: 80, r: 28, intens: 0.9 },
            { x: 130, y: 130, r: 25, intens: 0.7 },
            { x: 140, y: 180, r: 32, intens: 0.9 },
            { x: 160, y: 220, r: 20, intens: 0.6 }
        ]
    },
    blurry_leaf: {
        decision: 'retake',
        confidence: 0.210,
        predictions: [],
        crop_router: [],
        clip: [],
        validation: {
            quality: { ok: false, score: 0.28, blur: 82, brightness: 120, contrast: 38, resolution: [1280, 720], failures: ['high_motion_blur', 'suboptimal_contrast'] },
            segmentation: { detected: false, confidence: 0.0, num_detections: 0, ratio: 0.0 },
            area: null
        },
        advisory: {
            summary: "Diagnostic failed. Image quality checks detected extreme motion blur and low contrast.",
            symptoms: [],
            organic: [],
            chemical: [],
            prevention: [],
            expert: "No advisory generated due to quality validation failure."
        },
        latency: { quality_ms: 48, segmentation_ms: 0, extract_ms: 0, classification_ms: 0, explain_ms: 0, advisory_ms: 0, total_ms: 48 }
    }
};

/* ==========================================================================
   APP STATE MANAGEMENT
   ========================================================================== */

let currentScenario = SCENARIOS.tomato_late_blight;
let appHistory = [];
let uploadState = {
    file: null,
    isProcessing: false
};

/* ==========================================================================
   INITIALIZATION & TAB ROUTING
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initViewRouting();
    initUploadHandlers();
    initScenarioSelect();
    initAdvisoryTabs();
    initGradcamSlider();
    initSettingsPanel();
    initCitationAccordion();
    
    // Load simulation history logs
    loadHistoryData();
    populateHistoryTable();
    populateMapPins();

    // Trigger initial scenario load into DOM UI
    updateUIElements();
});

// View Navigation Router
function initViewRouting() {
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.content-view');
    const viewTitle = document.getElementById('viewTitle');
    const sidebar = document.getElementById('sidebar');
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const menuToggleBtn = document.getElementById('menuToggleBtn');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetView = item.getAttribute('data-view');
            
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            views.forEach(v => {
                v.classList.remove('active');
                if (v.id === `view-${targetView}`) {
                    v.classList.add('active');
                }
            });

            // Set Title Header
            viewTitle.textContent = item.querySelector('span').textContent;

            // Close mobile sidebar if open
            sidebar.classList.remove('mobile-open');
        });
    });

    // Sidebar collapse action
    sidebarCollapseBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // Mobile Hamburger button toggle
    menuToggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('mobile-open');
    });
}

/* ==========================================================================
   PHOTO SCANNERS / UPLOADER HANDLERS
   ========================================================================== */

function initUploadHandlers() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const selectBtn = document.getElementById('selectBtn');
    const resetBtn = document.getElementById('resetBtn');
    const dropzonePreview = document.getElementById('dropzonePreview');
    const dropzoneContent = document.querySelector('.dropzone-content');

    selectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleUpload(e.target.files[0]);
        }
    });

    // Drag over animations
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleUpload(e.dataTransfer.files[0]);
        }
    });

    resetBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetScanner();
    });
}

function handleUpload(file) {
    uploadState.file = file;
    uploadState.isProcessing = true;

    const dropzonePreview = document.getElementById('dropzonePreview');
    const dropzoneContent = document.querySelector('.dropzone-content');
    const emptyResultState = document.getElementById('emptyResultState');
    const resultsContainer = document.getElementById('resultsContainer');
    
    // Hide empty states, show loading previews
    dropzoneContent.style.display = 'none';
    dropzonePreview.style.display = 'flex';
    emptyResultState.style.display = 'none';
    resultsContainer.style.display = 'block';

    // Build canvas base loading screen
    drawInitialUploadCanvas();
    
    // Execute mock stepper progress
    runPipelineSimulation();
}

function resetScanner() {
    uploadState.file = null;
    uploadState.isProcessing = false;

    const dropzonePreview = document.getElementById('dropzonePreview');
    const dropzoneContent = document.querySelector('.dropzone-content');
    const emptyResultState = document.getElementById('emptyResultState');
    const resultsContainer = document.getElementById('resultsContainer');
    const steps = document.querySelectorAll('.step');

    // Clean inputs
    document.getElementById('fileInput').value = '';
    
    dropzoneContent.style.display = 'flex';
    dropzonePreview.style.display = 'none';
    emptyResultState.style.display = 'flex';
    resultsContainer.style.display = 'none';

    // Reset pipeline steps
    steps.forEach(step => {
        step.className = 'step disabled';
        const badge = step.querySelector('.step-badge');
        badge.className = 'step-badge badge-pending';
        badge.textContent = 'Pending';
        step.querySelector('.step-details').style.display = 'none';
    });
}

/* ==========================================================================
   SCENARIO LOADS
   ========================================================================== */

function initScenarioSelect() {
    const select = document.getElementById('demoScenario');
    select.addEventListener('change', (e) => {
        const scenarioKey = e.target.value;
        currentScenario = SCENARIOS[scenarioKey];
        
        // If image is uploaded, rerun pipeline automatically
        if (uploadState.file) {
            runPipelineSimulation();
        } else {
            updateUIElements();
        }
    });
}

/* ==========================================================================
   PIPELINE TELEMETRY SIMULATOR
   ========================================================================== */

async function runPipelineSimulation() {
    const steps = [
        { id: 'step-quality', duration: 400, run: runQualityStep },
        { id: 'step-segmentation', duration: 600, run: runSegmentationStep },
        { id: 'step-area', duration: 300, run: runAreaStep },
        { id: 'step-extraction', duration: 350, run: runExtractionStep },
        { id: 'step-classification', duration: 500, run: runClassificationStep }
    ];

    // Reset steps first
    document.querySelectorAll('.step').forEach(step => {
        step.className = 'step disabled';
        const badge = step.querySelector('.step-badge');
        badge.className = 'step-badge badge-pending';
        badge.textContent = 'Pending';
        step.querySelector('.step-details').style.display = 'none';
    });

    // Scroll results pane into view on mobile
    if (window.innerWidth < 1200) {
        document.getElementById('resultsContainer').scrollIntoView({ behavior: 'smooth' });
    }

    // Hide results charts while simulating pipeline
    document.getElementById('resultsContainer').style.opacity = '0.3';

    for (let i = 0; i < steps.length; i++) {
        const s = steps[i];
        const stepEl = document.getElementById(s.id);
        
        stepEl.className = 'step active';
        const badge = stepEl.querySelector('.step-badge');
        badge.className = 'step-badge badge-active';
        badge.textContent = 'Analyzing';

        // Await delay
        await new Promise(resolve => setTimeout(resolve, s.duration));

        // Execute step logic
        const success = s.run(stepEl, badge);
        
        if (!success) {
            // Terminate pipeline if critical validation fails
            break;
        }
    }

    // Reveal results fully
    document.getElementById('resultsContainer').style.opacity = '1.0';
    
    // Draw all leaf canvases
    renderCanvases();
    
    // Render detail charts and cards
    updateUIElements();

    // Log the scan to history if success
    if (uploadState.file) {
        logToHistory();
    }
}

// Pipeline Steps Logic
function runQualityStep(el, badge) {
    const q = currentScenario.validation.quality;
    const details = document.getElementById('details-quality');
    
    details.style.display = 'block';
    details.innerHTML = `
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div>Blur index: <strong>${q.blur}</strong></div>
            <div>Brightness: <strong>${q.brightness}</strong></div>
            <div>Contrast: <strong>${q.contrast}</strong></div>
            <div>Resolution: <strong>${q.resolution[0]}x${q.resolution[1]}</strong></div>
        </div>
    `;

    if (q.ok) {
        el.className = 'step completed';
        badge.className = 'step-badge badge-pass';
        badge.textContent = 'Pass';
        return true;
    } else {
        el.className = 'step active'; // Keep warning highlight
        badge.className = 'step-badge badge-fail';
        badge.textContent = 'Rejected';
        details.innerHTML += `<div style="color:var(--status-fail); font-weight:600; margin-top:8px;">Quality checks failed: ${q.failures.join(', ')}</div>`;
        return false;
    }
}

function runSegmentationStep(el, badge) {
    const s = currentScenario.validation.segmentation;
    const details = document.getElementById('details-segmentation');
    
    details.style.display = 'block';
    
    if (s.detected) {
        details.innerHTML = `
            <div>Leaves detected: <strong>${s.num_detections}</strong></div>
            <div>Segmentation confidence: <strong>${(s.confidence * 100).toFixed(0)}%</strong></div>
        `;
        el.className = 'step completed';
        badge.className = 'step-badge badge-pass';
        badge.textContent = 'Isolated';
        return true;
    } else {
        details.innerHTML = `<div style="color:var(--status-fail); font-weight:600;">No foliage detected in frame.</div>`;
        el.className = 'step active';
        badge.className = 'step-badge badge-fail';
        badge.textContent = 'Failed';
        return false;
    }
}

function runAreaStep(el, badge) {
    const a = currentScenario.validation.area;
    const details = document.getElementById('details-area');
    
    if (!a) {
        el.className = 'step disabled';
        badge.className = 'step-badge badge-pending';
        badge.textContent = 'Skipped';
        return false;
    }

    details.style.display = 'block';
    details.innerHTML = `<div>Leaf cover ratio: <strong>${(a.ratio * 100).toFixed(0)}%</strong></div>`;

    if (a.ok) {
        el.className = 'step completed';
        badge.className = 'step-badge badge-pass';
        badge.textContent = 'Pass';
        return true;
    } else {
        el.className = 'step completed'; // Non-critical fail doesn't stop pipeline
        badge.className = 'step-badge badge-fail';
        badge.textContent = 'Suboptimal';
        details.innerHTML += `<div style="color:var(--status-warn); font-weight:500; margin-top:4px;">Validation warning: ${a.failure}</div>`;
        return true;
    }
}

function runExtractionStep(el, badge) {
    const details = document.getElementById('details-extraction');
    details.style.display = 'block';
    details.innerHTML = `<div>Standardized shape size: <strong>260 x 260 px</strong></div><div>Flat padding applied: <strong>15%</strong></div>`;
    
    el.className = 'step completed';
    badge.className = 'step-badge badge-pass';
    badge.textContent = 'Completed';
    return true;
}

function runClassificationStep(el, badge) {
    const details = document.getElementById('details-classification');
    details.style.display = 'block';
    
    if (currentScenario.predictions.length > 0) {
        const topPred = currentScenario.predictions[0];
        details.innerHTML = `<div>Best diagnosis: <strong>${topPred.label}</strong></div><div>Confidence score: <strong>${(topPred.confidence * 100).toFixed(1)}%</strong></div>`;
        el.className = 'step completed';
        badge.className = 'step-badge badge-pass';
        badge.textContent = 'Classified';
        return true;
    } else {
        details.innerHTML = `<div style="color:var(--status-fail);">Classifier was not executed.</div>`;
        el.className = 'step disabled';
        badge.className = 'step-badge badge-pending';
        badge.textContent = 'Skipped';
        return false;
    }
}

/* ==========================================================================
   CANVAS DYNAMIC LEAF GRAPHICS GENERATOR
   ========================================================================== */

function drawInitialUploadCanvas() {
    const canvas = document.getElementById('originalCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 400;
    canvas.height = 300;

    // Draw dark loading state on canvas
    ctx.fillStyle = '#0a0f0c';
    ctx.fillRect(0, 0, 400, 300);
    
    ctx.fillStyle = '#17b864';
    ctx.font = 'Outfit 14px';
    ctx.textAlign = 'center';
    ctx.fillText("Raw Upload Loaded. Analyzing...", 200, 150);
}

function renderCanvases() {
    if (currentScenario === SCENARIOS.blurry_leaf) {
        drawBlurryCanvases();
        return;
    }

    drawOriginalCanvas();
    drawMaskCanvas();
    drawCropCanvas();
    drawGradcamCanvases();
}

// Helper to draw standard vector leaf shapes on HTML Canvas
function drawLeafShape(ctx, cx, cy, w, h, leafColor) {
    ctx.beginPath();
    // Move to leaf tip
    ctx.moveTo(cx, cy - h/2);
    // Draw leaf left edge
    ctx.quadraticCurveTo(cx - w/2, cy - h/10, cx - w/6, cy + h/3);
    // Draw stem connector
    ctx.lineTo(cx, cy + h/2);
    // Draw leaf right edge
    ctx.quadraticCurveTo(cx + w/2, cy - h/10, cx, cy - h/2);
    
    ctx.fillStyle = leafColor;
    ctx.fill();
    ctx.strokeStyle = '#1d3525';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Draw central vein
    ctx.beginPath();
    ctx.moveTo(cx, cy - h/2);
    ctx.lineTo(cx, cy + h/2);
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.stroke();

    // Draw side veins
    const veinOffsets = [-h/4, -h/10, h/10, h/4];
    veinOffsets.forEach(offset => {
        // Left side veins
        ctx.beginPath();
        ctx.moveTo(cx, cy + offset);
        ctx.quadraticCurveTo(cx - w/4, cy + offset - 10, cx - w/4, cy + offset - 15);
        ctx.strokeStyle = 'rgba(255,255,255,0.1)';
        ctx.stroke();
        // Right side veins
        ctx.beginPath();
        ctx.moveTo(cx, cy + offset);
        ctx.quadraticCurveTo(cx + w/4, cy + offset - 10, cx + w/4, cy + offset - 15);
        ctx.stroke();
    });
}

function drawDiseaseSpots(ctx, cx, cy, w, h, spots, spotColor) {
    spots.forEach(s => {
        const grad = ctx.createRadialGradient(s.x, s.y, s.r * 0.1, s.x, s.y, s.r);
        grad.addColorStop(0, spotColor);
        grad.addColorStop(0.4, 'rgba(120, 80, 50, 0.6)');
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
    });
}

function drawOriginalCanvas() {
    const canvas = document.getElementById('originalCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 400;
    canvas.height = 300;

    // Soil background
    ctx.fillStyle = '#181512';
    ctx.fillRect(0, 0, 400, 300);

    // Soil textures/noise
    ctx.fillStyle = '#211d19';
    for (let i = 0; i < 30; i++) {
        ctx.beginPath();
        ctx.arc(Math.random() * 400, Math.random() * 300, Math.random() * 6 + 2, 0, Math.PI * 2);
        ctx.fill();
    }

    // Draw Leaf
    drawLeafShape(ctx, 200, 150, 160, 240, currentScenario.leaf_color);

    // Draw spots
    drawDiseaseSpots(ctx, 200, 150, 160, 240, currentScenario.spots, currentScenario.spot_color);
}

function drawMaskCanvas() {
    const canvas = document.getElementById('maskCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 400;
    canvas.height = 300;

    // Copy original canvas contents
    const orig = document.getElementById('originalCanvas');
    ctx.drawImage(orig, 0, 0);

    // Draw semi-transparent bounding mask overlay
    ctx.save();
    
    // Mask region path (identical leaf shape)
    ctx.beginPath();
    ctx.moveTo(200, 30);
    ctx.quadraticCurveTo(200 - 80, 126, 200 - 26, 230);
    ctx.lineTo(200, 270);
    ctx.quadraticCurveTo(200 + 80, 126, 200, 30);
    
    ctx.fillStyle = 'rgba(255, 80, 80, 0.35)'; // Red transparent mask
    ctx.fill();

    // Bounding Outline border
    ctx.strokeStyle = '#f24444';
    ctx.lineWidth = 3;
    ctx.shadowColor = '#f24444';
    ctx.shadowBlur = 10;
    ctx.stroke();

    ctx.restore();

    // Bounding Box text tag
    ctx.fillStyle = 'rgba(242, 68, 68, 0.9)';
    ctx.fillRect(110, 10, 85, 20);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 10px Inter';
    ctx.fillText("leaf 96.2%", 120, 24);
}

function drawCropCanvas() {
    const canvas = document.getElementById('cropCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 260;
    canvas.height = 260;

    // Flat isolated background (standardized 260x260 model canvas)
    ctx.fillStyle = '#0c100d';
    ctx.fillRect(0, 0, 260, 260);

    // Render scaled down, isolated clean leaf shape
    drawLeafShape(ctx, 130, 130, 130, 200, currentScenario.leaf_color);

    // Shift spots offset to match scaled coordinates
    const scale = 200 / 240;
    const scaledSpots = currentScenario.spots.map(s => {
        return {
            x: 130 + (s.x - 200) * scale,
            y: 130 + (s.y - 150) * scale,
            r: s.r * scale
        };
    });

    drawDiseaseSpots(ctx, 130, 130, 130, 200, scaledSpots, currentScenario.spot_color);
}

function drawGradcamCanvases() {
    // 1. Clean Leaf background base
    const cleanCanvas = document.getElementById('gradcamCleanCanvas');
    const cleanCtx = cleanCanvas.getContext('2d');
    cleanCanvas.width = 260;
    cleanCanvas.height = 260;
    
    const cropCanvas = document.getElementById('cropCanvas');
    cleanCtx.drawImage(cropCanvas, 0, 0);

    // 2. Heatmap Canvas
    const heatCanvas = document.getElementById('gradcamHeatCanvas');
    const heatCtx = heatCanvas.getContext('2d');
    heatCanvas.width = 260;
    heatCanvas.height = 260;

    // Clear heatmap background (fully transparent)
    heatCtx.clearRect(0, 0, 260, 260);

    // Draw thermal gradients inside spots
    const scale = 200 / 240;
    currentScenario.heatmap_spots.forEach(hs => {
        const sx = 130 + (hs.x - 200) * scale;
        const sy = 130 + (hs.y - 150) * scale;
        const sr = hs.r * scale;

        const grad = heatCtx.createRadialGradient(sx, sy, sr * 0.05, sx, sy, sr);
        // Traditional thermal gradient: Red -> Orange -> Yellow -> Green -> Alpha
        grad.addColorStop(0, 'rgba(255, 0, 0, 1.0)');
        grad.addColorStop(0.25, 'rgba(255, 140, 0, 0.85)');
        grad.addColorStop(0.5, 'rgba(255, 235, 0, 0.7)');
        grad.addColorStop(0.75, 'rgba(0, 255, 0, 0.3)');
        grad.addColorStop(1, 'rgba(0,0,0,0)');

        heatCtx.fillStyle = grad;
        heatCtx.beginPath();
        heatCtx.arc(sx, sy, sr, 0, Math.PI * 2);
        heatCtx.fill();
    });
}

function drawBlurryCanvases() {
    // Original Canvas
    const orig = document.getElementById('originalCanvas');
    const origCtx = orig.getContext('2d');
    orig.width = 400;
    orig.height = 300;

    // Draw generic soil
    origCtx.fillStyle = '#1c1712';
    origCtx.fillRect(0, 0, 400, 300);

    // Draw extremely blurred green shape representing leaf
    origCtx.save();
    origCtx.filter = 'blur(30px)';
    origCtx.fillStyle = '#3a6341';
    origCtx.beginPath();
    origCtx.arc(200, 150, 80, 0, Math.PI*2);
    origCtx.fill();
    origCtx.restore();

    // Draw alert overlay text
    origCtx.fillStyle = 'rgba(242, 68, 68, 0.75)';
    origCtx.fillRect(0, 0, 400, 300);
    origCtx.fillStyle = '#fff';
    origCtx.font = 'bold 16px Outfit';
    origCtx.textAlign = 'center';
    origCtx.fillText("Motion Blur Detected (Fail)", 200, 140);
    origCtx.font = '12px Inter';
    origCtx.fillText("System aborts pipeline; no classification possible.", 200, 165);

    // Reset Mask & Crop canvases
    const mask = document.getElementById('maskCanvas');
    mask.getContext('2d').clearRect(0,0,400,300);
    
    const crop = document.getElementById('cropCanvas');
    crop.getContext('2d').clearRect(0,0,260,260);

    // Reset Grad-CAM
    document.getElementById('gradcamCleanCanvas').getContext('2d').clearRect(0,0,260,260);
    document.getElementById('gradcamHeatCanvas').getContext('2d').clearRect(0,0,260,260);
}

/* ==========================================================================
   UI DATA RENDERING / DYNAMIC BINDINGS
   ========================================================================== */

function updateUIElements() {
    renderDecisionBanner();
    renderPredictionsList();
    renderAdvisoryCard();
    renderCrossCheck();
    renderLatencyReport();
    renderModelInspectorGauges();
}

function renderDecisionBanner() {
    const banner = document.getElementById('decisionBanner');
    const title = document.getElementById('decisionTitle');
    const subtitle = document.getElementById('decisionSubtitle');
    const val = document.getElementById('decisionValue');
    const icon = document.getElementById('decisionIcon');

    // Reset styles
    banner.className = 'decision-banner';
    
    val.textContent = `${(currentScenario.confidence * 100).toFixed(1)}%`;

    if (currentScenario.decision === 'high_confidence') {
        icon.textContent = '🟢';
        title.textContent = 'AUTO-ACCEPT DIAGNOSIS';
        subtitle.textContent = 'High system confidence, safe for autonomous action';
    } else if (currentScenario.decision === 'expert_review') {
        banner.classList.add('warn');
        icon.textContent = '⚠️';
        title.textContent = 'EXPERT REVIEW QUEUE';
        subtitle.textContent = 'Diverted to human experts for verification';
    } else {
        banner.classList.add('fail');
        icon.textContent = '❌';
        title.textContent = 'RETAKE REQUESTED';
        subtitle.textContent = 'Image resolution/quality constraints failed';
    }
}

function renderPredictionsList() {
    const list = document.getElementById('predictionsList');
    list.innerHTML = '';

    if (currentScenario.predictions.length === 0) {
        list.innerHTML = `<div style="text-align:center; color:var(--text-muted); font-size:13px; padding: 20px 0;">No classification output available.</div>`;
        return;
    }

    currentScenario.predictions.forEach(p => {
        const item = document.createElement('div');
        item.className = 'prediction-item';
        
        item.innerHTML = `
            <div class="prediction-info">
                <span class="prediction-label">${p.label}</span>
                <span class="prediction-score">${(p.confidence * 100).toFixed(1)}%</span>
            </div>
            <div class="prediction-bar-bg">
                <div class="prediction-bar-fill" style="width: 0%;"></div>
            </div>
        `;
        list.appendChild(item);
        
        // Trigger bar fill animation
        setTimeout(() => {
            item.querySelector('.prediction-bar-fill').style.width = `${p.confidence * 100}%`;
        }, 100);
    });
}

function renderAdvisoryCard() {
    const content = document.getElementById('advisoryContent');
    const scenario = currentScenario;

    if (scenario.decision === 'retake') {
        content.innerHTML = `
            <div style="font-size:14px; line-height:1.6;">
                <p style="font-weight:600; color:var(--status-fail); margin-bottom:10px;">${scenario.advisory.summary}</p>
                <p style="margin-bottom:12px;">The CPL Crop Doctor quality control engine requires a replacement leaf photo. Please follow these guidelines:</p>
                <div class="advisory-note" style="margin-top:0;">
                    <ul style="margin:0; padding:0; list-style:none;">
                        <li style="margin-bottom:6px; padding-left:16px;"><strong>Avoid Motion Blur:</strong> Hold the camera steady; ensure auto-focus snaps directly to leaf surface.</li>
                        <li style="margin-bottom:6px; padding-left:16px;"><strong>Improve Contrast:</strong> Ensure the background soil is dark or diffuse, avoiding harsh sunlight shadows.</li>
                        <li style="margin-bottom:6px; padding-left:16px;"><strong>Leaf Proportions:</strong> Center the leaf in the lens so it covers between 15% and 80% of the viewfinder.</li>
                    </ul>
                </div>
            </div>
        `;
        document.getElementById('citationToggle').style.display = 'none';
        return;
    }

    document.getElementById('citationToggle').style.display = 'flex';
    
    // Set active tab content
    const activeTab = document.querySelector('.advisory-tab.active').getAttribute('data-tab');
    renderActiveTabContent(activeTab);
}

function renderActiveTabContent(tabName) {
    const content = document.getElementById('advisoryContent');
    const a = currentScenario.advisory;
    
    let listHTML = '';

    if (tabName === 'symptoms') {
        listHTML = `<ul>${a.symptoms.map(s => `<li>${s}</li>`).join('')}</ul>`;
    } else if (tabName === 'organic') {
        listHTML = `<ul>${a.organic.map(o => `<li>${o}</li>`).join('')}</ul>`;
    } else if (tabName === 'chemical') {
        listHTML = `<ul>${a.chemical.map(c => `<li>${c}</li>`).join('')}</ul>`;
    } else if (tabName === 'prevention') {
        listHTML = `<ul>${a.prevention.map(p => `<li>${p}</li>`).join('')}</ul>`;
    }

    content.innerHTML = `
        <p style="font-style:italic; margin-bottom:12px; font-size:13px; color:var(--text-bright);">${a.summary}</p>
        ${listHTML}
        <div class="advisory-note">
            <strong>⚠️ Agronomist Note:</strong> ${a.expert}
        </div>
    `;

    // Render citations
    const citationsList = document.getElementById('citationsList');
    citationsList.innerHTML = '';
    
    a.citations.forEach(c => {
        const item = document.createElement('div');
        item.className = 'citation-item';
        item.innerHTML = `
            <div class="citation-meta">
                <span>${c.source}</span>
                <span>Similarity: ${(c.similarity * 100).toFixed(0)}%</span>
            </div>
            <p class="citation-text">"${c.text}"</p>
        `;
        citationsList.appendChild(item);
    });
}

function initAdvisoryTabs() {
    const tabs = document.querySelectorAll('.advisory-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const tabName = tab.getAttribute('data-tab');
            renderActiveTabContent(tabName);
        });
    });
}

function initCitationAccordion() {
    const header = document.getElementById('citationToggle');
    const list = document.getElementById('citationsList');

    header.addEventListener('click', () => {
        header.classList.toggle('open');
        if (list.style.display === 'none') {
            list.style.display = 'flex';
        } else {
            list.style.display = 'none';
        }
    });
}

/* ==========================================================================
   MODEL INSPECTOR (VIEW 2) INTERACTION
   ========================================================================== */

function initGradcamSlider() {
    const slider = document.getElementById('opacitySlider');
    const val = document.getElementById('opacityVal');
    const heatCanvas = document.getElementById('gradcamHeatCanvas');

    slider.addEventListener('input', (e) => {
        const op = e.target.value;
        val.textContent = `${op}%`;
        heatCanvas.style.opacity = op / 100;
    });

    const methodVanilla = document.getElementById('methodVanilla');
    const methodSmooth = document.getElementById('methodSmooth');

    methodVanilla.addEventListener('click', () => {
        methodVanilla.classList.add('active');
        methodSmooth.classList.remove('active');
        // Rerender/modify canvas
        drawGradcamCanvases();
    });

    methodSmooth.addEventListener('click', () => {
        methodSmooth.classList.add('active');
        methodVanilla.classList.remove('active');
        
        // Simulate SmoothGrad heat map adjustments
        const canvas = document.getElementById('gradcamHeatCanvas');
        const ctx = canvas.getContext('2d');
        // Redraw heatmap slightly smoother/less noisy
        drawGradcamCanvases();
        // Blur heatmap canvas slightly to mimic SmoothGrad aggregation
        ctx.save();
        ctx.filter = 'blur(4px)';
        ctx.drawImage(canvas, 0, 0);
        ctx.restore();
    });
}

function renderModelInspectorGauges() {
    const gaugeFill = document.getElementById('fusedGaugeFill');
    const gaugeValue = document.getElementById('fusedGaugeValue');
    
    // Formula calculation
    const conf = currentScenario.confidence;
    gaugeValue.textContent = `${(conf * 100).toFixed(0)}%`;

    // SVG dash offsets (Dasharray perimeter: 2 * PI * r = 2 * 3.14159 * 40 = 251.2)
    const strokeOffset = 251.2 - (251.2 * conf);
    gaugeFill.style.strokeDashoffset = strokeOffset;

    // Set colors matching decisions
    if (currentScenario.decision === 'high_confidence') {
        gaugeFill.style.stroke = 'var(--accent-green)';
    } else if (currentScenario.decision === 'expert_review') {
        gaugeFill.style.stroke = 'var(--status-warn)';
    } else {
        gaugeFill.style.stroke = 'var(--status-fail)';
    }

    // Populate weighted signals list
    const signalsList = document.getElementById('signalsWeightsList');
    signalsList.innerHTML = '';

    const weights = getStoredWeights();
    
    const signals = [
        { name: 'Quality Assessment', val: currentScenario.validation.quality.score, w: weights.quality },
        { name: 'YOLO Mask Segment', val: currentScenario.validation.segmentation.confidence, w: weights.seg },
        { name: 'Leaf Cover Area Ratio', val: currentScenario.validation.area ? currentScenario.validation.area.score : 0.0, w: weights.area },
        { name: 'EfficientNet Top-1 Prob', val: currentScenario.predictions.length > 0 ? currentScenario.predictions[0].confidence : 0.0, w: weights.top1 },
        { name: 'Classification Margin Gap', val: currentScenario.predictions.length > 1 ? (currentScenario.predictions[0].confidence - currentScenario.predictions[1].confidence) : 0.0, w: weights.gap }
    ];

    signals.forEach(s => {
        const row = document.createElement('div');
        row.className = 'signal-row';
        row.innerHTML = `
            <span class="signal-name">${s.name}</span>
            <span class="signal-math">${s.val.toFixed(2)} x ${s.w.toFixed(2)} = <strong>${(s.val * s.w).toFixed(3)}</strong></span>
        `;
        signalsList.appendChild(row);
    });
}

function renderCrossCheck() {
    const banner = document.getElementById('crosscheckBanner');
    const badge = document.getElementById('crosscheckBadge');
    const summary = document.getElementById('crosscheckSummary');
    const tbody = document.getElementById('crosscheckTableBody');

    tbody.innerHTML = '';

    if (currentScenario.decision === 'retake') {
        banner.className = 'crosscheck-banner fail';
        badge.textContent = '⚠️ Validation Aborted';
        badge.style.color = 'var(--status-fail)';
        summary.textContent = 'No classification models were executed because image quality requirements failed.';
        
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No logs available.</td></tr>`;
        return;
    }

    // Check crop agreements
    const primaryCrop = currentScenario.predictions[0].crop;
    const routerCrop = currentScenario.crop_router[0].crop;
    const clipCrop = currentScenario.clip[0].crop;

    const allAgree = (primaryCrop === routerCrop) && (primaryCrop === clipCrop);

    if (allAgree) {
        banner.className = 'crosscheck-banner';
        badge.textContent = '✓ Taxonomy Confirmed';
        badge.style.color = 'var(--accent-green)';
        summary.textContent = `All models unanimously confirm crop family is ${primaryCrop}. Confidence indices verified.`;
    } else {
        banner.className = 'crosscheck-banner warn';
        badge.textContent = '⚠️ Discordant Agreement';
        badge.style.color = 'var(--status-warn)';
        summary.textContent = `Crop family voting discrepant: EfficientNet = ${primaryCrop}, Router = ${routerCrop}, CLIP = ${clipCrop}. Verification required.`;
    }

    const rows = [
        { pipe: 'EfficientNetV2-B2 (Joint Class)', prediction: currentScenario.predictions[0].crop, score: currentScenario.predictions[0].confidence, agree: true },
        { pipe: 'Hierarchical Router (Per-crop head)', prediction: routerCrop, score: currentScenario.crop_router[0].confidence, agree: routerCrop === primaryCrop },
        { pipe: 'OpenAI CLIP Foundation (Zero-shot)', prediction: clipCrop, score: currentScenario.clip[0].similarity, agree: clipCrop === primaryCrop }
    ];

    rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${r.pipe}</strong></td>
            <td>${r.prediction} Leaf</td>
            <td>${(r.score * 100).toFixed(1)}%</td>
            <td>
                <span class="badge-status ${r.agree ? 'pass' : 'fail'}">
                    ${r.agree ? 'Agreement' : 'Discordant'}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderLatencyReport() {
    const total = document.getElementById('latencyTotalVal');
    const timeline = document.getElementById('latencyTimeline');

    total.textContent = `${currentScenario.latency.total_ms} ms`;
    timeline.innerHTML = '';

    const stages = [
        { name: 'Quality Assessment (OpenCV)', ms: currentScenario.latency.quality_ms },
        { name: 'Leaf Segmentation (YOLOv8)', ms: currentScenario.latency.segmentation_ms },
        { name: 'Clean Crop Extraction', ms: currentScenario.latency.extract_ms },
        { name: 'EfficientNetV2 Classification', ms: currentScenario.latency.classification_ms },
        { name: 'SmoothGrad Heatmap Overlay', ms: currentScenario.latency.explain_ms },
        { name: 'Advisory RAG Query (Gemini)', ms: currentScenario.latency.advisory_ms }
    ];

    const maxMs = currentScenario.latency.total_ms || 1;

    stages.forEach(s => {
        const item = document.createElement('div');
        item.className = 'latency-stage';
        const percent = (s.ms / maxMs) * 100;
        
        item.innerHTML = `
            <div class="latency-stage-info">
                <span class="latency-stage-name">${s.name}</span>
                <span class="latency-stage-ms">${s.ms} ms</span>
            </div>
            <div class="latency-stage-bar-bg">
                <div class="latency-stage-bar-fill" style="width: 0%;"></div>
            </div>
        `;
        timeline.appendChild(item);

        setTimeout(() => {
            item.querySelector('.latency-stage-bar-fill').style.width = `${percent}%`;
        }, 100);
    });
}

/* ==========================================================================
   LOGS & MAP SIMULATION (VIEW 3)
   ========================================================================== */

function loadHistoryData() {
    const stored = localStorage.getItem('cpl_crop_history');
    if (stored) {
        appHistory = JSON.parse(stored);
    } else {
        // Populate baseline mock history logs
        appHistory = [
            { id: 'req_a1b2', date: '2026-06-12 08:05', crop: 'Tomato', disease: 'Late Blight', conf: 0.924, decision: 'high_confidence' },
            { id: 'req_c3d4', date: '2026-06-12 07:42', crop: 'Sugarcane', disease: 'Rust', conf: 0.684, decision: 'expert_review' },
            { id: 'req_e5f6', date: '2026-06-12 07:12', crop: 'Cotton', disease: 'Healthy', conf: 0.965, decision: 'high_confidence' },
            { id: 'req_g7h8', date: '2026-06-12 06:30', crop: 'Tomato', disease: 'Blurry Photo', conf: 0.210, decision: 'retake' },
            { id: 'req_i9j0', date: '2026-06-11 15:24', crop: 'Rice', disease: 'Brown Spot', conf: 0.742, decision: 'expert_review' }
        ];
        saveHistoryData();
    }
}

function saveHistoryData() {
    localStorage.setItem('cpl_crop_history', JSON.stringify(appHistory));
}

function logToHistory() {
    const topPred = currentScenario.predictions[0] || { crop: 'Unknown', disease: currentScenario.validation.quality.ok ? 'Unidentified' : 'Quality Defect' };
    const newLog = {
        id: 'req_' + Math.random().toString(36).substring(2, 6),
        date: new Date().toISOString().replace('T', ' ').substring(0, 16),
        crop: topPred.crop,
        disease: topPred.disease,
        conf: currentScenario.confidence,
        decision: currentScenario.decision
    };

    appHistory.unshift(newLog);
    // Keep max 20 logs in demo local storage
    if (appHistory.length > 20) appHistory.pop();
    saveHistoryData();

    populateHistoryTable();
    populateMapPins();
    
    // Update KPI counters
    document.getElementById('kpiTotalScans').textContent = appHistory.length + 137; // Offset to look real
}

function populateHistoryTable() {
    const tbody = document.getElementById('historyTableBody');
    tbody.innerHTML = '';

    appHistory.forEach(log => {
        const tr = document.createElement('tr');
        
        let labelClass = 'badge-pending';
        let labelName = 'Retake';
        if (log.decision === 'high_confidence') {
            labelClass = 'badge-pass';
            labelName = 'Auto-Accept';
        } else if (log.decision === 'expert_review') {
            labelClass = 'badge-active';
            labelName = 'Review Queue';
        } else {
            labelClass = 'badge-fail';
        }

        tr.innerHTML = `
            <td>${log.date}</td>
            <td><strong>${log.crop}</strong></td>
            <td>${log.disease}</td>
            <td style="font-family:monospace;">${(log.conf * 100).toFixed(1)}%</td>
            <td><span class="step-badge ${labelClass}">${labelName}</span></td>
        `;
        tbody.appendChild(tr);

        // Click on history loads logs
        tr.addEventListener('click', () => {
            // Find appropriate scenario
            let scenarioKey = 'tomato_late_blight';
            if (log.disease === 'Rust') scenarioKey = 'sugarcane_rust';
            if (log.disease === 'Blurry Photo' || log.decision === 'retake') scenarioKey = 'blurry_leaf';
            
            // Switch dropdown
            document.getElementById('demoScenario').value = scenarioKey;
            currentScenario = SCENARIOS[scenarioKey];
            
            // Simulate loading past scan data
            uploadState.file = new File([""], "history_log.jpg");
            handleUpload(uploadState.file);

            // Switch view back to Diagnostics Tab
            document.querySelector('[data-view="diagnostics"]').click();
        });
    });

    // Add search listener
    const search = document.getElementById('logSearch');
    search.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach(r => {
            const txt = r.textContent.toLowerCase();
            r.style.display = txt.includes(query) ? '' : 'none';
        });
    });
}

function populateMapPins() {
    const map = document.getElementById('mapVectorContainer');
    
    // Clear old pins
    map.querySelectorAll('.map-pin').forEach(p => p.remove());

    // Simulated pin coordinate nodes mapping to agricultural sectors
    const pinLocations = [
        { x: '18%', y: '25%', type: 'green', tooltip: 'Tomato Field (Req: 219a) - Healthy' },
        { x: '26%', y: '32%', type: 'red', tooltip: 'Tomato Field (Req: req_a1b2) - Late Blight Outbreak' },
        { x: '46%', y: '28%', type: 'yellow', tooltip: 'Sugarcane Plot (Req: req_c3d4) - Rust Infection' },
        { x: '58%', y: '34%', type: 'green', tooltip: 'Sugarcane Sector B - Healthy' },
        { x: '78%', y: '52%', type: 'green', tooltip: 'Rice Zone 4 - Healthy' },
        { x: '82%', y: '64%', type: 'yellow', tooltip: 'Rice Outpost (Req: req_i9j0) - Brown Spot' },
        { x: '34%', y: '72%', type: 'green', tooltip: 'Cotton Belt C - Healthy' }
    ];

    // Create tooltip element if missing
    let tooltip = document.getElementById('mapTooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'mapTooltip';
        tooltip.className = 'map-tooltip';
        document.body.appendChild(tooltip);
    }

    pinLocations.forEach(loc => {
        const pin = document.createElement('div');
        pin.className = `map-pin map-pin-${loc.type}`;
        pin.style.left = loc.x;
        pin.style.top = loc.y;

        pin.addEventListener('mouseenter', (e) => {
            tooltip.textContent = loc.tooltip;
            tooltip.style.display = 'block';
            tooltip.style.left = (e.pageX + 15) + 'px';
            tooltip.style.top = (e.pageY - 15) + 'px';
        });

        pin.addEventListener('mousemove', (e) => {
            tooltip.style.left = (e.pageX + 15) + 'px';
            tooltip.style.top = (e.pageY - 15) + 'px';
        });

        pin.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
        });

        map.appendChild(pin);
    });
}

/* ==========================================================================
   CONFIGURATION PANELS (VIEW 4)
   ========================================================================== */

const STORAGE_KEY_WEIGHTS = 'cpl_crop_weights';
const STORAGE_KEY_THRESHOLDS = 'cpl_crop_thresholds';

function initSettingsPanel() {
    const topkSlider = document.getElementById('topkSlider');
    const topkVal = document.getElementById('topkVal');

    topkSlider.addEventListener('input', (e) => {
        topkVal.textContent = e.target.value;
    });

    // Thresholds Sliders
    const threshHigh = document.getElementById('thresholdHigh');
    const threshHighVal = document.getElementById('thresholdHighVal');
    const threshMed = document.getElementById('thresholdMedium');
    const threshMedVal = document.getElementById('thresholdMediumVal');

    threshHigh.addEventListener('input', (e) => {
        threshHighVal.textContent = (e.target.value / 100).toFixed(2);
    });

    threshMed.addEventListener('input', (e) => {
        threshMedVal.textContent = (e.target.value / 100).toFixed(2);
    });

    // Load initial config values
    const thresholds = getStoredThresholds();
    threshHigh.value = thresholds.high * 100;
    threshHighVal.textContent = thresholds.high.toFixed(2);
    threshMed.value = thresholds.medium * 100;
    threshMedVal.textContent = thresholds.medium.toFixed(2);

    const weights = getStoredWeights();
    document.getElementById('wQuality').value = weights.quality;
    document.getElementById('wSeg').value = weights.seg;
    document.getElementById('wArea').value = weights.area;
    document.getElementById('wTop1').value = weights.top1;
    document.getElementById('wGap').value = weights.gap;
    document.getElementById('wCross').value = weights.cross;

    updateWeightTotalBadge();

    // Inputs listener for weights sum validation
    const weightInputs = [
        document.getElementById('wQuality'),
        document.getElementById('wSeg'),
        document.getElementById('wArea'),
        document.getElementById('wTop1'),
        document.getElementById('wGap'),
        document.getElementById('wCross')
    ];

    weightInputs.forEach(input => {
        input.addEventListener('change', updateWeightTotalBadge);
    });

    // Buttons
    document.getElementById('saveSettingsBtn').addEventListener('click', () => {
        saveConfig();
        alert("Settings Saved Successfully!");
        // Rerender Inspector gauge with updated weights formulas
        renderModelInspectorGauges();
    });

    document.getElementById('resetSettingsBtn').addEventListener('click', () => {
        localStorage.removeItem(STORAGE_KEY_WEIGHTS);
        localStorage.removeItem(STORAGE_KEY_THRESHOLDS);
        
        // Reload page defaults
        window.location.reload();
    });
}

function updateWeightTotalBadge() {
    const sum = getWeightSum();
    const badge = document.getElementById('weightSumBadge');
    
    badge.textContent = sum.toFixed(2);
    if (Math.abs(sum - 1.0) < 0.001) {
        badge.className = 'badge-status pass';
    } else {
        badge.className = 'badge-status fail';
    }
}

function getWeightSum() {
    return parseFloat(document.getElementById('wQuality').value) +
           parseFloat(document.getElementById('wSeg').value) +
           parseFloat(document.getElementById('wArea').value) +
           parseFloat(document.getElementById('wTop1').value) +
           parseFloat(document.getElementById('wGap').value) +
           parseFloat(document.getElementById('wCross').value);
}

function getStoredWeights() {
    const stored = localStorage.getItem(STORAGE_KEY_WEIGHTS);
    if (stored) return JSON.parse(stored);
    
    // Page Defaults
    return { quality: 0.10, seg: 0.15, area: 0.10, top1: 0.30, gap: 0.15, cross: 0.20 };
}

function getStoredThresholds() {
    const stored = localStorage.getItem(STORAGE_KEY_THRESHOLDS);
    if (stored) return JSON.parse(stored);
    
    return { high: 0.80, medium: 0.50 };
}

function saveConfig() {
    const weights = {
        quality: parseFloat(document.getElementById('wQuality').value),
        seg: parseFloat(document.getElementById('wSeg').value),
        area: parseFloat(document.getElementById('wArea').value),
        top1: parseFloat(document.getElementById('wTop1').value),
        gap: parseFloat(document.getElementById('wGap').value),
        cross: parseFloat(document.getElementById('wCross').value)
    };

    const thresholds = {
        high: parseFloat(document.getElementById('thresholdHigh').value) / 100,
        medium: parseFloat(document.getElementById('thresholdMedium').value) / 100
    };

    localStorage.setItem(STORAGE_KEY_WEIGHTS, JSON.stringify(weights));
    localStorage.setItem(STORAGE_KEY_THRESHOLDS, JSON.stringify(thresholds));
}
