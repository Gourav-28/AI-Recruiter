import os
import sys
import json
import gzip
import io
import heapq
import re
from datetime import datetime
import requests
import numpy as np

# ==========================================
# 🛡️ DYNAMIC ENVIRONMENTAL HYBRID LAYER
# ==========================================
USE_API_MODE = False
semantic_model = None
util = None

# Automatically trigger Cloud API mode if running inside a live Streamlit process
if "streamlit" in sys.modules:
    USE_API_MODE = True
else:
    try:
        from sentence_transformers import SentenceTransformer, util
        # Local configuration for offline evaluation sandboxes
        MODEL_PATH = "./all-MiniLM-L6-v2"
        if os.path.exists(MODEL_PATH) and os.listdir(MODEL_PATH):
            semantic_model = SentenceTransformer(MODEL_PATH, local_files_only=True)
        else:
            semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        USE_API_MODE = False
    except Exception:
        # Fallback to API if local deep-learning libraries are missing/broken
        USE_API_MODE = True

# ==========================================
# 🌐 HUGGING FACE SERVERLESS INFERENCE API
# ==========================================
def fetch_embeddings_api(texts):
    """
    Queries Hugging Face's public API to fetch text embeddings.
    Requires absolutely zero local system memory overhead.
    """
    API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
    try:
        payload = {"inputs": texts, "options": {"wait_for_model": True}}
        response = requests.post(API_URL, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

# ==========================================
# 🛡️ POLYMORPHIC STREAM READER
# ==========================================
def stream_candidates(uploaded_file):
    if isinstance(uploaded_file, str):
        if uploaded_file.endswith('.gz'):
            with gzip.open(uploaded_file, 'rt', encoding='utf-8') as f:
                for line in f:
                    if line.strip(): yield json.loads(line)
        else:
            with open(uploaded_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.startswith('['):
                    for item in json.loads(content): yield item
                else:
                    f.seek(0)
                    for line in f:
                        if line.strip(): yield json.loads(line)
        return

    try:
        uploaded_file.seek(0)
        raw_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        
        if raw_bytes.startswith(b'\x1f\x8b'):
            decompressed = gzip.decompress(raw_bytes).decode("utf-8")
            f_text = io.StringIO(decompressed)
            for line in f_text:
                if line.strip(): yield json.loads(line)
        else:
            decoded = raw_bytes.decode("utf-8").strip()
            if decoded.startswith('['):
                for item in json.loads(decoded): yield item
            else:
                f_text = io.StringIO(decoded)
                for line in f_text:
                    if line.strip(): yield json.loads(line)
    except Exception as e:
        raise RuntimeError(f"Streaming ingestion failure: {str(e)}")

# --- FIREWALL FILTRATION (ANTI-FRAUD LOGIC) ---
def is_honeypot(candidate):
    CURRENT_YEAR = 2026
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_history = candidate.get("career_history", []) or candidate.get("experience", []) or []
    skills_list = candidate.get("skills", [])
    
    if not candidate.get("candidate_id"): return True
    if not signals.get("verified_email", True) and not signals.get("verified_phone", True): return True  
    if signals.get("profile_completeness_score", 100) < 20: return True
        
    years_exp = profile.get("years_of_experience", 0) or 0
    if years_exp > 3 and not career_history: return True
        
    for exp in career_history:
        years_at_company = exp.get("years_at_company") or exp.get("years") or 0
        company_meta = exp.get("company", {})
        if isinstance(company_meta, dict):
            founded_year = company_meta.get("founded_year") or company_meta.get("founded")
            if founded_year:
                try:
                    if years_at_company > (CURRENT_YEAR - int(founded_year)): return True
                except (ValueError, TypeError): pass

    expert_skills = sum(1 for s in skills_list if isinstance(s, dict) and str(s.get("proficiency", "")).lower() in ["expert", "advanced", "master"])
    if expert_skills >= 5 and years_exp == 0: return True
    return False

# ==========================================
# ⚡ HYBRID MATCHING & RE-RANKING ENGINE
# ==========================================
def rank_retrieved_pool(candidate_pool, jd_text):
    batch_texts = []
    valid_candidates = []

    for candidate in candidate_pool:
        skills_list = candidate.get("skills", [])
        candidate_skills = [str(s.get("name", "")).strip() for s in skills_list if s.get("name")]
        if not candidate_skills: continue
        batch_texts.append(f"Expertise and technical skills include: {', '.join(candidate_skills)}.")
        valid_candidates.append(candidate)

    if not batch_texts: return []

    similarities = None

    # STRATEGY PATH A: Web Mode (Execute Serverless Online Processing)
    if USE_API_MODE:
        jd_res = fetch_embeddings_api([jd_text])
        batch_res = fetch_embeddings_api(batch_texts)
        
        if jd_res and batch_res and isinstance(jd_res, list) and isinstance(batch_res, list):
            try:
                v1 = np.array(jd_res[0])
                v2 = np.array(batch_res)
                dot = np.dot(v2, v1)
                n1 = np.linalg.norm(v1)
                n2 = np.linalg.norm(v2, axis=1)
                similarities = (dot / (n1 * n2)).tolist()
            except Exception:
                similarities = None

    # STRATEGY PATH B: CLI Evaluation Mode (Execute Heavy Local Transformers)
    if similarities is None and semantic_model is not None:
        try:
            jd_embedding = semantic_model.encode(jd_text, convert_to_tensor=True)
            batch_embeddings = semantic_model.encode(batch_texts, convert_to_tensor=True)
            similarities = util.cos_sim(jd_embedding, batch_embeddings)[0].tolist()
        except Exception:
            similarities = None

    # STRATEGY PATH C: Emergency Lexical Fallback (Jaccard Intersections)
    if similarities is None:
        jd_tokens = set(re.findall(r'\w+', jd_text.lower()))
        similarities = []
        for text in batch_texts:
            text_tokens = set(re.findall(r'\w+', text.lower()))
            intersection = jd_tokens.intersection(text_tokens)
            union = jd_tokens.union(text_tokens)
            similarities.append(len(intersection) / len(union) if union else 0.0)

    # Compile and Normalize Ratings Curve
    raw_scored_pool = []
    max_raw_score = 0.0

    for idx, candidate in enumerate(valid_candidates):
        similarity = similarities[idx]
        skill_score = max(0.0, similarity * 100 * 1.2)
        
        profile = candidate.get("profile", {})
        signals = candidate.get("redrob_signals", {})
        
        years_exp = profile.get("years_of_experience", 0) or 0
        exp_score = 100 if 4 <= years_exp <= 8 else (80 if years_exp > 8 else ((years_exp / 4) * 100 if years_exp > 0 else 0))
        base_tech_score = (skill_score * 0.70) + (exp_score * 0.30)

        # Behavioral Adjustments Map
        multiplier = 1.0
        if (signals.get("recruiter_response_rate", 1.0) or 0.0) > 0.80: multiplier *= 1.15
        if (signals.get("interview_completion_rate", 1.0) or 0.0) < 0.60: multiplier *= 0.70
        if (signals.get("github_activity_score", -1) or -1) > 65: multiplier *= 1.10

        raw_score = base_tech_score * multiplier
        if raw_score > max_raw_score: max_raw_score = raw_score
        raw_scored_pool.append((raw_score, candidate))

    final_ranked_results = []
    divisor = max_raw_score if max_raw_score > 0 else 1.0
    
    for raw_score, candidate in raw_scored_pool:
        normalized_score = max(0.0, min(100.0, (raw_score / divisor) * 100))
        c_id = str(candidate.get("candidate_id") or "Unknown").strip()
        p = candidate.get("profile", {})
        reasoning = f"{p.get('anonymized_name', 'Candidate')} matched vectors at {round(normalized_score, 1)}% alignment."
        final_ranked_results.append((normalized_score, c_id, reasoning))
        
    return final_ranked_results

# --- STREAM ORCHESTRATOR ---
def get_top_100(uploaded_file, jd_requirements):
    jd_words = set(re.findall(r'\w+', jd_requirements.lower()))
    RETRIEVAL_LIMIT = 1500
    stage1_heap = []
    
    for candidate in stream_candidates(uploaded_file):
        if is_honeypot(candidate): continue
        matched_count = sum(2 if str(s.get("name", "")).lower() in jd_words else 1 for s in candidate.get("skills", []) if any(w in jd_words for w in str(s.get("name", "")).lower().split()))
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        
        if len(stage1_heap) < RETRIEVAL_LIMIT:
            heapq.heappush(stage1_heap, (matched_count, candidate_id, candidate))
        elif matched_count > stage1_heap[0][0]:
            heapq.heappushpop(stage1_heap, (matched_count, candidate_id, candidate))

    high_value_pool = [item[2] for item in stage1_heap]
    if not high_value_pool: return []

    all_scored_candidates = rank_retrieved_pool(high_value_pool, jd_requirements)
    perfectly_sorted = sorted(all_scored_candidates, key=lambda x: (-float(x[0]), str(x[1])))
    top_100 = perfectly_sorted[:100]
    
    while len(top_100) < 100:
        top_100.append((0.0, f"PADDING_ID_{len(top_100)}", "Fallback baseline profile overlay."))
        
    return top_100
