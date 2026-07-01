import os
import gzip
import json
import io
import heapq
import re
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# Define your local model folder path inside your repository
MODEL_PATH = "./all-MiniLM-L6-v2"

try:
    import streamlit as st
    @st.cache_resource
    def load_shared_model():
        # Step A: Check if a local compiled model exists and is not empty
        if os.path.exists(MODEL_PATH) and os.listdir(MODEL_PATH):
            try:
                return SentenceTransformer(MODEL_PATH, local_files_only=True)
            except Exception:
                pass  # Fallback to download if local files are corrupted
                
        # Step B: Download from Hugging Face directly into container cache
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Step C: Try writing locally, pass silently if the server filesystem is read-only
        try:
            if not os.path.exists(MODEL_PATH):
                model.save(MODEL_PATH)
        except Exception:
            pass 
        return model
        
    semantic_model = load_shared_model()
except ImportError:
    # Pure CLI Fallback Configuration for rank.py
    if os.path.exists(MODEL_PATH) and os.listdir(MODEL_PATH):
        try:
            semantic_model = SentenceTransformer(MODEL_PATH, local_files_only=True)
        except Exception:
            semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    else:
        semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        try:
            semantic_model.save(MODEL_PATH)
        except Exception:
            pass

# GLOBAL PERFORMANCE CACHE

if '_cached_jd_text' not in globals():
    _cached_jd_text = ""
if '_cached_jd_embedding' not in globals():
    _cached_jd_embedding = None


# --- 1. MEMORY-SAFE HYBRID STREAMING INGESTOR ---
def stream_candidates(uploaded_file):
    """
    Cloud-resilient stream reader. Safely processes uploaded raw bytes 
    without causing permission errors or filesystem crashes.
    """
    uploaded_file.seek(0)
    # Read the first two bytes to check for official Gzip magic numbers
    magic_number = uploaded_file.read(2)
    uploaded_file.seek(0)
    
    # If the file is a true compressed .gz file
    if magic_number == b'\x1f\x8b':
        with gzip.GzipFile(fileobj=uploaded_file, mode='rb') as gz:
            text_stream = io.TextIOWrapper(gz, encoding='utf-8')
            for line in text_stream:
                if line.strip():
                    yield json.loads(line)
    else:
        # If the file is standard uncompressed JSONL or a JSON array
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        
        if file_bytes.startswith(b'['):
            data = json.loads(file_bytes.decode("utf-8"))
            for item in data:
                yield item
        else:
            text_stream = io.StringIO(file_bytes.decode("utf-8"))
            for line in text_stream:
                if line.strip():
                    yield json.loads(line)


# --- 2. FIREWALL FILTRATION (ANTI-FRAUD LOGIC) ---
def is_honeypot(candidate):
    """
    Evaluates profile integrity markers and structural anomalies to trap
    programmatic honeypots before they reach the vector layer.
    """
    CURRENT_YEAR = 2026
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_history = candidate.get("career_history", []) or candidate.get("experience", [])
    skills_list = candidate.get("skills", [])
    
    # Base validations
    if not candidate.get("candidate_id"):
        return True
    if not signals.get("verified_email", True) and not signals.get("verified_phone", True):
        return True  
    if signals.get("profile_completeness_score", 100) < 20:
        return True
        
    years_exp = profile.get("years_of_experience", 0) or 0
    if years_exp > 3 and not career_history:
        return True
        
    
    for exp in career_history:
        years_at_company = exp.get("years_at_company", 0) or exp.get("years", 0) or 0
        company_meta = exp.get("company", {})
        
        if isinstance(company_meta, dict):
            founded_year = company_meta.get("founded_year") or company_meta.get("founded")
            if founded_year:
                try:
                    company_lifespan = CURRENT_YEAR - int(founded_year)
                    if years_at_company > company_lifespan:
                        return True
                except (ValueError, TypeError):
                    pass

   
    expert_skills_count = 0
    for skill in skills_list:
        if isinstance(skill, dict):
            proficiency = str(skill.get("proficiency", "")).lower()
            level = skill.get("level", 0)
            if proficiency in ["expert", "advanced", "master"] or level >= 5:
                expert_skills_count += 1
                
    if expert_skills_count >= 5 and years_exp == 0:
        return True
        
    return False


# RE-RANKER
def rank_retrieved_pool(candidate_pool, jd_embedding):
    """
    Processes only the top filtered candidates using heavy AI matrix transformations.
    Applies Relative Max Normalization to dynamically prevent score saturation.
    """
    batch_texts = []
    valid_candidates = []

    for candidate in candidate_pool:
        skills_list = candidate.get("skills", [])
        candidate_skills = [str(s.get("name", "")).strip() for s in skills_list if s.get("name")]
        
        if not candidate_skills:
            continue
            
        text_profile = f"Expertise and technical skills include: {', '.join(candidate_skills)}."
        batch_texts.append(text_profile)
        valid_candidates.append(candidate)

    if not batch_texts:
        return []

    batch_embeddings = semantic_model.encode(batch_texts, convert_to_tensor=True, show_progress_bar=False)
    similarities = util.cos_sim(jd_embedding, batch_embeddings)[0].tolist()

    raw_scored_pool = []
    max_raw_score = 0.0


    for idx, candidate in enumerate(valid_candidates):
        similarity = similarities[idx]
        skill_score = max(0.0, similarity * 100 * 1.2)
        
        profile = candidate.get("profile", {})
        signals = candidate.get("redrob_signals", {})
        
        years_exp = profile.get("years_of_experience", 0) or 0
        if 4 <= years_exp <= 8:
            exp_score = 100
        elif years_exp > 8:
            exp_score = 80
        else:
            exp_score = (years_exp / 4) * 100 if years_exp > 0 else 0

        base_tech_score = (skill_score * 0.70) + (exp_score * 0.30)

    
        multiplier = 1.0
        response_rate = signals.get("recruiter_response_rate", 1.0) or 0.0
        if response_rate > 0.80:
            multiplier *= 1.15
        elif response_rate < 0.40:
            multiplier *= 0.75

        interview_completion = signals.get("interview_completion_rate", 1.0) or 0.0
        if interview_completion < 0.60:
            multiplier *= 0.70

        github_score = signals.get("github_activity_score", -1) or -1
        if github_score > 65:
            multiplier *= 1.10

        last_active_str = signals.get("last_active_date", "")
        if last_active_str:
            try:
                last_active = datetime.strptime(last_active_str.split("T")[0], "%Y-%m-%d")
                days_inactive = (datetime(2026, 6, 28) - last_active).days
                if days_inactive > 90:
                    multiplier *= 0.85
            except Exception:
                pass

        if signals.get("open_to_work_flag") is True:
            multiplier *= 1.05

        raw_score = base_tech_score * multiplier
        if raw_score > max_raw_score:
            max_raw_score = raw_score
            
        raw_scored_pool.append((raw_score, candidate, similarity))


    final_ranked_results = []
    if max_raw_score == 0:
        max_raw_score = 1.0
        
    for raw_score, candidate, similarity in raw_scored_pool:
        normalized_score = max(0.0, min(100.0, (raw_score / max_raw_score) * 100))
        
        profile = candidate.get("profile", {})
        signals = candidate.get("redrob_signals", {})
        
        c_id = str(candidate.get("candidate_id") or "Unknown_ID").strip()
        name = profile.get("anonymized_name", "Anonymous Candidate")
        title = profile.get("current_title", "Engineer")
        resp_rate_pct = int((signals.get("recruiter_response_rate", 0) or 0) * 100)
        
        reasoning = (
            f"{name} ({title}) matched core vectors at {round(normalized_score, 1)}%. "
            f"Maintains a verified {resp_rate_pct}% interaction rate on-platform."
        )
        
        final_ranked_results.append((normalized_score, c_id, reasoning))
        
    return final_ranked_results



def get_top_100(uploaded_file, jd_requirements):
    """
    Executes a high-performance two-stage retrieval pipeline.
    Ensures strict alignment with challenge submission rules via deterministic sorting.
    """
    global _cached_jd_text, _cached_jd_embedding
    
    jd_words = set(re.findall(r'\w+', jd_requirements.lower()))
    
    RETRIEVAL_LIMIT = 1500
    stage1_heap = []
    

    for candidate in stream_candidates(uploaded_file):
        if is_honeypot(candidate):
            continue
            
        skills_list = candidate.get("skills", [])
        matched_count = 0
        for s in skills_list:
            skill_name = str(s.get("name", "")).lower()
            if skill_name in jd_words:
                matched_count += 2
            elif any(word in jd_words for word in skill_name.split()):
                matched_count += 1

        candidate_id = str(candidate.get("candidate_id", "")).strip()
        
      
        if len(stage1_heap) < RETRIEVAL_LIMIT:
            heapq.heappush(stage1_heap, (matched_count, candidate_id, candidate))
        else:
            if matched_count > stage1_heap[0][0]:
                heapq.heappushpop(stage1_heap, (matched_count, candidate_id, candidate))

    high_value_pool = [item[2] for item in stage1_heap]
    
    if not high_value_pool:
        return []


    if _cached_jd_text != jd_requirements or _cached_jd_embedding is None:
        _cached_jd_text = jd_requirements
        _cached_jd_embedding = semantic_model.encode(jd_requirements, convert_to_tensor=True)

   
    all_scored_candidates = rank_retrieved_pool(high_value_pool, _cached_jd_embedding)
    
   
    perfectly_sorted = sorted(
        all_scored_candidates, 
        key=lambda x: (-float(x[0]), str(x[1]))
    )
    
  
    top_100 = perfectly_sorted[:100]
    return top_100
