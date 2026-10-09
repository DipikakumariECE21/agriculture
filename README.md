# Patra — Crop Disease Detection System

AI/ML camp project by **Dipika Kumari**, Dept. of Electronics & Communication Engineering,
Government Women Polytechnic · guided by **Rashid Sir**.

A multi-page Python (Flask) website that screens crop leaves for disease from a single photo,
with a scroll-driven film on the home page (250 frames scrubbed by scroll position).

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deploy (Render, free)

Netlify only hosts static files, so it can't run this Flask app. Use Render instead:

1. Sign in at https://render.com with GitHub.
2. **New → Blueprint**, pick this repository. Render reads `render.yaml` and deploys.
3. The site goes live at `https://patra-crop-disease.onrender.com` (or similar).

The free plan sleeps after 15 minutes without visitors; the first visit after that takes ~30 s.
The scan log starts empty after every redeploy.

## Pages

| Route | What it does |
|---|---|
| `/` | Scroll-driven film (field → row → diseased leaf), problem, pipeline, library preview |
| `/detect` | Upload / drag-drop / paste / sample → lesion map, class probabilities, severity, advice |
| `/diseases` | Filterable, searchable library of 8 conditions |
| `/diseases/<slug>` | Symptoms, causes, management for one condition |
| `/how-it-works` | Architecture, pipeline, methodology, requirements, test cases |
| `/project` | Report summary, objectives, limitations, future scope, report download |
| `/history` | SQLite scan log with stats |
| `POST /api/analyze` | JSON API — multipart field `image` |

## How detection works (`analyzer.py`)

1. Quality gate — Laplacian-variance sharpness and exposure.
2. HSV conversion, leaf segmentation (green mask → morphological close → hole fill).
3. Lesion isolation — brown/necrotic, rust, chlorotic yellow, powdery white, enclosed necrotic centres.
4. Connected-component spot statistics (count, largest spot).
5. Feature scores for 7 classes → softmax probabilities, severity band, guidance.

It is a transparent, rule-based colour/texture model — a preliminary screen, not a diagnosis.
The feature pipeline is the baseline a CNN (e.g. trained on PlantVillage) can replace.

## Frames & watermark

`static/frames/0001–0250.webp` were produced from the supplied zip by
`scripts/prepare_frames.py`, which removes the Gemini sparkle watermark by estimating its alpha
map across all frames, inverting the blend, then inpainting the residual edge.

```bash
pip install opencv-python-headless
python scripts/prepare_frames.py path/to/extracted_frames --out static
```
