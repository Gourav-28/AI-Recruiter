# ResuRank AI — Two-Stage Talent Matching Engine

ResuRank AI is a production-grade semantic recruitment pipeline that processes 100,000+ candidates on a local CPU in seconds. It uses a **Two-Stage Retrieval & Re-ranking Architecture** with Sentence Transformers (`all-MiniLM-L6-v2`) for deep semantic matching.

Built for **Hack2Skill India Run Hackathon** — Automated Candidate Ranking & Honeypot Filter Pipeline.

## Features

- **Two-Stage Architecture:** Lightweight heuristic filter discards 98.5% of noise in milliseconds, then AI re-ranks top 1,500 candidates
- **Memory-Safe Streaming:** Reads 100k+ candidate files line-by-line — never loads entire dataset into RAM
- **Anti-Fraud Detection:** Honeypot filter catches bot profiles, keyword stuffers, and incomplete records
- **Behavioral Overlay:** Adjusts scores by response rate, GitHub activity, interview completion, open-to-work status
- **Relative Max Normalization:** Spreads scores dynamically instead of saturating at 100%
- **Dual UI:** Streamlit dashboard or Flask REST API + static frontend

## Quick Start

```bash
pip install -r requirements.txt
```

**Option 1 — Flask Server + Frontend:**
```bash
python server.py
# Open http://127.0.0.1:5000
```

**Option 2 — Streamlit UI:**
```bash
streamlit run app.py
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves frontend dashboard |
| `/api/mock` | GET | Returns 100 mock-ranked candidates |
| `/api/upload` | POST | Upload a JSON/JSONL candidate file |
| `/api/rank` | POST | Run ranking pipeline on uploaded file |
| `/api/candidate/<id>` | GET | Get single candidate details |

## Project Structure

```
├── app.py              # Streamlit UI
├── server.py           # Flask REST API server
├── engine.py           # Two-stage ranking engine
├── frontend/           # Static frontend assets
│   ├── index.html
│   ├── css/style.css
│   └── js/script.js
├── requirements.txt
└── README.md
```

## How It Works

1. **Upload** candidate profiles (JSON/JSONL) via the sidebar
2. **Stage 1 — Heuristic Net:** Filters 100k profiles to top 1,500 using keyword/token matching
3. **Stage 2 — Semantic AI:** Encodes candidates and JD with SentenceTransformer, computes cosine similarity
4. **Behavioral Overlay:** Adjusts scores by recruiter response rate, interview completion, GitHub activity, recency
5. **Output:** Top 100 ranked candidates with explainable reasoning + downloadable `submission.csv`
