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
