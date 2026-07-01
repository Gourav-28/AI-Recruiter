
# ResuRank AI: High-Performance Two-Stage Talent Matching Engine 🚀

ResuRank AI is a production-grade, end-to-end semantic recruitment and candidate ranking pipeline built to process massive talent pools instantly. Utilizing a **Two-Stage Retrieval & Re-ranking Architecture**, this system cleanly handles datasets of over 100,000+ candidates on a local CPU—dropping execution times from 40+ minutes down to a few seconds without sacrificing accuracy.

Built with **Streamlit**, **PyTorch**, and **Sentence-Transformers**, the engine blends heavy deep-learning semantic understanding with behavioral metadata overlays to generate an accurate, non-saturating candidate compatibility curve.

---

## ⚡ Mathematical & Structural Bottlenecks Solved

1. **The Row-by-Row Inference Loop Stagger:** Traditional implementations run individual forward passes through neural networks for each candidate sequentially. ResuRank implements **Vectorized Batch Processing**, passing consolidated text arrays directly to PyTorch's underlying C++ layers for matrix multiplication.
2. **The 100k CPU AI Wall:** Running deep-learning transformer tokenization on 100,000 profiles locally stalls standard systems. This pipeline introduces a **Two-Stage Retrieval Architecture** that filters out 98.5% of the noise in milliseconds using lightweight heuristic token checks before letting the AI touch the refined top 1,500.
3. **Score Saturation (The Ceiling Effect):** Rigid math limits score outputs at a flat 100%, causing top-tier candidates to tie arbitrarily. This engine implements **Relative Max Normalization**, dynamically spreading candidates across a clean bell curve relative to the top performer in the pool.

---

## 🛠️ System Architecture

The pipeline processes data through a highly optimized, memory-safe data flow:

```text
[Raw candidates.jsonl (100k+)] 
              │
              ▼
┌──────────────────────────┐
│ STAGE 1: Heuristic Net   │ ──► Drops 98.5% of non-matching profiles in milliseconds
└──────────────────────────┘
              │ (Top 1,500 high-potential candidates)
              ▼
┌──────────────────────────┐
│ STAGE 2: Semantic AI     │ ──► Batched SentenceTransformer ('all-MiniLM-L6-v2')
└──────────────────────────┘
              │
              ▼
┌──────────────────────────┐
│ Behavioral Overlay Net   │ ──► Adjusts rankings based on real-world platform signals
└──────────────────────────┘
              │
              ▼
┌──────────────────────────┐
│ Relative Max Normalizer  │ ──► Scales data dynamically against the absolute best match
└──────────────────────────┘
              │
              ▼
    [Streamlit UI Dashboard (Top 100)]

```

---

## 📁 Repository Structure

```text
your-hackathon-repo/
│
├── README.md                   # System documentation and execution guide
├── requirements.txt            # Locked environment dependencies
├── submission_metadata.yaml    # Team and track validation metadata
│
├── rank.py                     # CLI Bridge Script (Entry point for evaluation server)
├── engine.py                   # Core logic (Streaming, Honeypots, Vector Re-ranking)
└── app.py                      # Streamlit Interactive UI / Sandbox Demo Frontend

```

---

## ⚙️ Environment Setup & Installation

Follow these steps to configure a clean, isolated environment to run the reproduction script or local dashboard.

### 1. Environment Initialization

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

> ⚙️ **Model Initialization Note:** The embedding layer runs in a flexible hybrid configuration. If the directory `./all-MiniLM-L6-v2` is absent, the system will securely download the model weights directly from Hugging Face during its first execution pass and cache them locally for all future offline instances.

---

## 🛡️ Stage 3 Verification & Anti-Fraud Firewall

ResuRank features a programmatic, procedural **Firewall Filtration Layer** inside `engine.py` designed to shield the neural network from adversarial inputs. It identifies and drops unverified programmatic bot tracking profiles or structural traps before they reach vector initialization:

* **Timeline Contradiction Filter:** Flags profiles where a candidate's claimed duration of experience at a target enterprise exceeds the foundational lifespan of the company itself.
* **Over-Proficiency Trap:** Intercepts accounts claiming maximum proficiency across an extensive array of skills while displaying zero total years of real-world industry experience.

---

## 🏆 Executing Submission Reproduction (The Golden Command)

For Stage 3 evaluation and code validation, execute the following single command from the root of the repository. This processes the target dataset through the pipeline and outputs the final, deterministically sorted 100-row file:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv

```

---

## 🌐 Running the Live Sandbox Interactive UI

To interact with the live matching engine dashboard, visual cues, and candidate breakdowns via the Streamlit web interface, run:

```bash
streamlit run app.py

```

```

```
