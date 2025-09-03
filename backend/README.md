# Ecards Simple - Backend API (Flask)

A minimal Flask API to store e-card drafts (including the template URI) on the backend.

Endpoints:
- GET /api/health
- POST /api/drafts
- GET /api/drafts/<draft_id>

Draft JSON schema:
{
  "id": "draft_123" | "d_<uuid>",   // optional on create, if omitted server creates one
  "title": "My e-card",
  "updatedAt": 1725360000000,         // epoch millis (server will set if omitted)
  "template": "assets/template1.png", // template URI/path
  "canvasSize": { "w": 900, "h": 600 },
  "data": {}                          // fabric.js JSON payload
}

Storage:
- Local JSON file at backend/data/drafts.json


## Setup

Create and activate a virtual environment (optional but recommended):

python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows PowerShell

Install dependencies:

pip install -r requirements.txt


## Run

Run the Flask server:

python app.py

- Server will listen on http://localhost:5001 by default.
- CORS is enabled to allow requests from file:// and http://localhost origins.


## Frontend Integration

The frontend index.html was updated to:
- Toggle between Local and API persistence via the "Storage: Local/API" button.
- Save drafts to the API when Storage=API. The server returns an id; the UI updates the URL with ?draft_id=ID.
- Load drafts from API when accessing a URL with ?draft_id=ID.
- Fallback to localStorage if API is not reachable during save or autosave.

If serving index.html using the file:// protocol, the frontend defaults API base to http://localhost:5001.
You can override API base for the frontend by setting localStorage key "ecards_api_base":

localStorage.setItem("ecards_api_base", "http://localhost:5001")

Then refresh the page.


## Example cURL

Create or update a draft:

curl -X POST http://localhost:5001/api/drafts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My ecard",
    "template": "assets/template1.png",
    "canvasSize": {"w": 900, "h": 600},
    "data": {"version": "5.3.0", "objects": []}
  }'

Fetch a draft by id:

curl http://localhost:5001/api/drafts/d_abc123