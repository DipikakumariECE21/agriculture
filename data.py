"""Static knowledge base: disease library, pipeline stages and project metadata."""

from __future__ import annotations

PROJECT = {
    "title": "Crop Disease Detection System",
    "student": "Dipika Kumari",
    "supervisor": "Rashid Sir",
    "department": "Electronics and Communication Engineering",
    "institute": "Government Women Polytechnic",
    "programme": "Diploma — AI/ML Camp Project",
    "report_file": "docs/Crop_Disease_Detection_Project_Report_Dipika_Kumari.docx",
}

DISEASES: list[dict] = [
    {
        "slug": "early-blight",
        "name": "Early Blight",
        "pathogen": "Alternaria solani",
        "type": "Fungal",
        "crops": ["Tomato", "Potato", "Brinjal"],
        "season": "Warm, humid weather (24–29 °C) with alternating wet and dry spells",
        "spread": "Moderate",
        "summary": "Brown lesions with concentric rings that start on older, lower leaves and climb the plant.",
        "symptoms": [
            "Dark brown spots, 3–12 mm, with concentric rings that look like a target board",
            "A yellow halo of chlorotic tissue around each lesion",
            "Lower, older leaves are affected first; heavy infection causes leaf drop",
            "Dark, sunken lesions can also appear on stems and fruit near the calyx",
        ],
        "causes": [
            "Fungal spores survive on infected crop debris and in soil",
            "Spores spread by wind, rain splash and contaminated tools",
            "Plants stressed by low nitrogen or heavy fruit load are more susceptible",
        ],
        "management": {
            "Cultural": [
                "Remove and destroy infected lower leaves as soon as spots appear",
                "Rotate with non-solanaceous crops for 2–3 seasons",
                "Mulch the soil to stop spores splashing onto leaves",
                "Water at the base of the plant, early in the day",
            ],
            "Biological / organic": [
                "Neem-based sprays or Trichoderma soil treatment as a preventive measure",
                "Maintain balanced nutrition to keep plants vigorous",
            ],
            "Chemical (on expert advice)": [
                "Protectant fungicides such as mancozeb or chlorothalonil, following label dose and interval",
            ],
        },
    },
    {
        "slug": "late-blight",
        "name": "Late Blight",
        "pathogen": "Phytophthora infestans",
        "type": "Oomycete",
        "crops": ["Potato", "Tomato"],
        "season": "Cool, moist conditions (10–24 °C) with long leaf-wetness periods",
        "spread": "Very fast",
        "summary": "Large, water-soaked lesions that turn dark brown to black and can collapse a field within days.",
        "symptoms": [
            "Pale green, water-soaked patches, usually starting at leaf tips and edges",
            "Lesions rapidly turn dark brown or black and lack concentric rings",
            "White, downy growth on the underside of leaves in humid mornings",
            "Firm, brown rot on tubers and greasy, dark patches on fruit",
        ],
        "causes": [
            "Infected seed tubers and volunteer plants carry the pathogen between seasons",
            "Spores travel long distances on wind and moist air",
            "Fog, drizzle and dense canopies accelerate infection",
        ],
        "management": {
            "Cultural": [
                "Plant certified, disease-free seed tubers and resistant varieties",
                "Destroy infected plants and cull piles immediately",
                "Improve air movement with proper plant spacing",
            ],
            "Biological / organic": [
                "Copper-based protectant sprays before infection periods",
            ],
            "Chemical (on expert advice)": [
                "Systemic fungicides (e.g. metalaxyl + mancozeb) only as recommended by the local agriculture officer",
            ],
        },
    },
    {
        "slug": "leaf-spot",
        "name": "Leaf Spot",
        "pathogen": "Cercospora spp. / Xanthomonas spp.",
        "type": "Fungal / Bacterial",
        "crops": ["Groundnut", "Soybean", "Chilli", "Tomato", "Okra"],
        "season": "Warm, wet weather with frequent rain splash",
        "spread": "Moderate",
        "summary": "Many small, round spots with pale or grey centres and dark margins scattered across the leaf.",
        "symptoms": [
            "Numerous small circular spots, 1–5 mm, scattered over the leaf blade",
            "Grey or tan centres with reddish-brown to dark borders",
            "Bacterial forms begin as water-soaked specks with a yellow halo",
            "Spots may merge, causing yellowing and early leaf fall",
        ],
        "causes": [
            "Spores or bacteria carried on seed, debris and weeds",
            "Rain splash and overhead irrigation move inoculum leaf to leaf",
            "Working in the crop while foliage is wet spreads bacteria",
        ],
        "management": {
            "Cultural": [
                "Use clean, treated seed and remove crop residue after harvest",
                "Avoid overhead irrigation and handling wet plants",
                "Rotate crops and control alternate weed hosts",
            ],
            "Biological / organic": [
                "Pseudomonas fluorescens seed treatment and foliar sprays",
                "Copper-based sprays for bacterial leaf spot",
            ],
            "Chemical (on expert advice)": [
                "Carbendazim or mancozeb for fungal leaf spot as per state recommendations",
            ],
        },
    },
    {
        "slug": "rust",
        "name": "Rust",
        "pathogen": "Puccinia spp. / Uromyces spp.",
        "type": "Fungal",
        "crops": ["Wheat", "Beans", "Groundnut", "Maize"],
        "season": "Moderate temperatures with dew or light rain",
        "spread": "Fast",
        "summary": "Raised, powdery pustules in orange to reddish-brown that leave rust-coloured dust on the fingers.",
        "symptoms": [
            "Small raised pustules, orange to reddish-brown, mostly on the underside",
            "Powdery spores rub off easily on fingers or cloth",
            "Yellow flecks on the upper surface opposite the pustules",
            "Severe infection dries leaves and reduces grain or pod filling",
        ],
        "causes": [
            "Wind-borne spores can travel hundreds of kilometres",
            "Volunteer plants and alternate hosts keep the fungus alive",
            "Dense, nitrogen-heavy crops create a humid micro-climate",
        ],
        "management": {
            "Cultural": [
                "Sow rust-resistant varieties recommended for your region",
                "Follow recommended sowing dates to avoid peak spore periods",
                "Destroy volunteer plants between seasons",
            ],
            "Biological / organic": [
                "Sulphur dust or wettable sulphur at early infection",
            ],
            "Chemical (on expert advice)": [
                "Triazole fungicides (e.g. propiconazole) as advised by the extension service",
            ],
        },
    },
    {
        "slug": "powdery-mildew",
        "name": "Powdery Mildew",
        "pathogen": "Erysiphe spp. / Podosphaera spp.",
        "type": "Fungal",
        "crops": ["Cucurbits", "Peas", "Okra", "Mango", "Grapes"],
        "season": "Dry days with cool, humid nights; shaded crops",
        "spread": "Fast",
        "summary": "White, flour-like patches on the upper leaf surface that spread until the whole leaf is coated.",
        "symptoms": [
            "White to grey powdery patches, first as small circles",
            "Patches enlarge and merge to cover leaves, stems and flowers",
            "Leaves turn yellow, curl and dry out prematurely",
            "Fruit set and quality are reduced",
        ],
        "causes": [
            "Unlike most fungi, it does not need free water on the leaf to infect",
            "Spores spread by wind; shaded and crowded plants are favoured",
            "Excess nitrogen produces soft, susceptible growth",
        ],
        "management": {
            "Cultural": [
                "Give plants full sun and enough spacing for airflow",
                "Remove heavily infected leaves early",
                "Avoid excess nitrogen fertiliser",
            ],
            "Biological / organic": [
                "Wettable sulphur or potassium bicarbonate sprays",
                "Diluted milk spray (1:9) as a home-garden preventive",
            ],
            "Chemical (on expert advice)": [
                "Hexaconazole or similar systemic fungicides per label",
            ],
        },
    },
    {
        "slug": "nutrient-chlorosis",
        "name": "Nutrient Chlorosis",
        "pathogen": "Nitrogen, iron or magnesium deficiency",
        "type": "Nutrient",
        "crops": ["All crops"],
        "season": "Poor or waterlogged soils, high pH, heavy rain leaching",
        "spread": "Non-infectious",
        "summary": "Diffuse yellowing without distinct spots — a nutrition problem, not a pathogen.",
        "symptoms": [
            "Uniform yellowing of older leaves (nitrogen) or of young leaves (iron)",
            "Yellow tissue between green veins (magnesium, iron)",
            "No distinct lesions, pustules or fungal growth",
            "Stunted growth and pale overall canopy",
        ],
        "causes": [
            "Insufficient fertiliser or nutrient leaching after heavy rain",
            "High soil pH locking up iron and manganese",
            "Waterlogging that damages roots and limits uptake",
        ],
        "management": {
            "Cultural": [
                "Get a soil test from the nearest Soil Health Card lab",
                "Improve drainage in waterlogged fields",
            ],
            "Biological / organic": [
                "Well-decomposed farmyard manure or vermicompost",
                "Green manuring with legumes",
            ],
            "Chemical (on expert advice)": [
                "Urea top-dressing for nitrogen; ferrous sulphate or MgSO₄ foliar sprays as indicated by the soil test",
            ],
        },
    },
    {
        "slug": "leaf-blast",
        "name": "Leaf Blast",
        "pathogen": "Magnaporthe oryzae",
        "type": "Fungal",
        "crops": ["Rice", "Finger millet"],
        "season": "High humidity, cloudy weather and night temperatures of 20–24 °C",
        "spread": "Very fast",
        "summary": "Spindle- or diamond-shaped lesions with grey centres and brown margins on rice leaves.",
        "symptoms": [
            "Spindle-shaped spots with grey-white centres and brown borders",
            "Lesions enlarge and merge, killing whole leaves",
            "Neck blast turns the panicle base black and causes empty grains",
        ],
        "causes": [
            "Air-borne spores from infected stubble and weeds",
            "Excess nitrogen and long dew periods",
            "Susceptible varieties in blast-prone regions",
        ],
        "management": {
            "Cultural": [
                "Grow blast-resistant varieties and avoid excess nitrogen",
                "Burn or deeply incorporate infected stubble",
            ],
            "Biological / organic": [
                "Pseudomonas fluorescens seed treatment and foliar sprays",
            ],
            "Chemical (on expert advice)": [
                "Tricyclazole sprays at boot-leaf and heading stages per state guidelines",
            ],
        },
    },
    {
        "slug": "healthy",
        "name": "Healthy Leaf",
        "pathogen": "Reference class",
        "type": "Healthy",
        "crops": ["All crops"],
        "season": "—",
        "spread": "—",
        "summary": "Uniform green colour, intact margins and no spots, pustules or powdery growth.",
        "symptoms": [
            "Even green colour typical of the variety",
            "Smooth surface without lesions, pustules or coating",
            "Leaf edges intact; no curling or premature drying",
        ],
        "causes": [
            "Balanced nutrition, good drainage and adequate spacing",
        ],
        "management": {
            "Keep it that way": [
                "Scout the field every 5–7 days, especially after rain",
                "Inspect the underside of leaves — many diseases start there",
                "Keep a photo log so changes are easy to spot",
            ],
        },
    },
]

DISEASE_BY_SLUG = {d["slug"]: d for d in DISEASES}

PIPELINE = [
    {"id": "01", "name": "Capture", "detail": "Phone or camera module photographs a single leaf in daylight."},
    {"id": "02", "name": "Quality check", "detail": "Sharpness (Laplacian variance) and exposure are measured before analysis."},
    {"id": "03", "name": "Preprocess", "detail": "Image is oriented, resized to 512 px and converted to HSV colour space."},
    {"id": "04", "name": "Segment", "detail": "Leaf tissue is separated from background; lesion pixels are isolated inside it."},
    {"id": "05", "name": "Classify", "detail": "Colour and spot features are scored against seven classes and normalised to probabilities."},
    {"id": "06", "name": "Advise", "detail": "Severity, confidence and management guidance are shown — and the scan is logged."},
]

METHODOLOGY = [
    ("Image collection", "Healthy and diseased leaf images are gathered from public datasets such as PlantVillage and from real field photographs."),
    ("Preprocessing", "Images are resized to a fixed resolution, pixel values normalised and irrelevant background reduced."),
    ("Dataset preparation", "Images are split into training, validation and test sets; augmentation (flips, rotation, brightness) improves robustness."),
    ("Model training", "A CNN — or a lightweight transfer-learning model for embedded devices — is trained on the labelled images."),
    ("Evaluation", "Accuracy, precision, recall, F1-score and the confusion matrix are measured on unseen test images."),
    ("Prediction", "A new leaf image is passed to the trained model to obtain the most probable class."),
    ("Output", "The predicted condition is shown with guidance that it is a preliminary indication, not an expert diagnosis."),
]

TEST_CASES = [
    ("Clear healthy leaf", "Healthy classification", "healthy"),
    ("Clear diseased leaf", "Matching disease class with severity", "disease"),
    ("Blurred photograph", "Low-confidence result with a sharpness warning", "warn"),
    ("Not a plant / unsupported crop", "Unsupported-image message", "reject"),
]

HARDWARE = [
    ("Camera / smartphone", "Captures the crop-leaf image"),
    ("Processing unit", "Computer or Raspberry Pi running the model"),
    ("Display", "Phone or computer screen for results"),
    ("Power supply", "Powers the embedded hardware in the field"),
    ("Communication module", "Optional Wi-Fi / Bluetooth / 4G for remote reporting"),
    ("Storage", "Holds datasets, models and captured images"),
]

SOFTWARE = [
    ("Python 3", "Core language for the model and this web server"),
    ("Flask", "Serves pages and the /api/analyze endpoint"),
    ("NumPy + Pillow", "Image maths, colour-space conversion and segmentation"),
    ("OpenCV", "Image operations and frame processing"),
    ("TensorFlow / PyTorch", "CNN training for the next model version"),
    ("SQLite", "Stores the scan history log"),
]

FUTURE_SCOPE = [
    "Real-time video detection from a phone camera",
    "Disease severity estimation per plant and per field",
    "Multi-crop support with a larger field dataset",
    "Offline on-device inference for low-connectivity villages",
    "Multilingual voice guidance in Hindi and regional languages",
    "Weather, soil-moisture and humidity sensor integration",
    "GPS-tagged disease maps for whole farms",
]
