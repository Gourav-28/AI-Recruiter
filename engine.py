#engine.py 
import gzip
import json
import io
import heapq
import re
from datetime import datetime

#Check if AI dependencies are available
_HAS_AI = False
try:
    from sentence_transformers import SentenceTransformer, util as _st_util
    _HAS_AI = True
except ImportError:
    _st_util = None

_semantic_model = None
_cached_jd_text = None
_cached_jd_embedding = None

def _get_semantic_model():
    global _semantic_model
    if not _HAS_AI:
        raise ImportError("sentence-transformers is not installed. Run: pip install sentence-transformers")
    if _semantic_model is None:
        print("Initializing Semantic AI Matching Engine...")
        _semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _semantic_model


#1 MEMORY-SAFE HYBRID STREAMING INGESTOR
def stream_candidates(uploaded_file):
    """
    Streams candidates safely by auto-detecting compressed Gzip format,
    plain JSONL line streams, or standard JSON arrays.
    """
    uploaded_file.seek(0)
    try:
        with gzip.open(uploaded_file, "rt", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    except (gzip.BadGzipFile, OSError):
        uploaded_file.seek(0)
        first_bytes = uploaded_file.read(10).strip()
        uploaded_file.seek(0)
        
        if first_bytes.startswith(b'['):
            content = uploaded_file.read().decode("utf-8")
            data = json.loads(content)
            for item in data:
                yield item
        else:
            for line_bytes in uploaded_file:
                line = line_bytes.decode("utf-8").strip()
                if line:
                    yield json.loads(line)


#2 FIREWALL FILTRATION (ANTI-FRAUD LOGIC)
def is_honeypot(candidate):
    """
    Evaluates profile integrity markers to catch programmatic bot accounts.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_history = candidate.get("career_history", [])
    
    if not candidate.get("candidate_id"):
        return True
    if not signals.get("verified_email", True) and not signals.get("verified_phone", True):
        return True  
    if signals.get("profile_completeness_score", 100) < 20:
        return True
    years_exp = profile.get("years_of_experience", 0) or 0
    if years_exp > 3 and not career_history:
        return True
        
    return False


#3 HIGH-SPEED VECTORIZED BATCH RE-RANKER
def rank_retrieved_pool(candidate_pool, jd_embedding):
    """
    Processes only the top filtered candidates using heavy AI matrix transformations.
    """
    final_ranked_results = []
    batch_texts = []
    valid_candidates = []

    # Format textual data for the transformer
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

    # Run AI vector conversion on the refined 1,500 chunk
    model = _get_semantic_model()
    batch_embeddings = model.encode(batch_texts, convert_to_tensor=True, show_progress_bar=False)
    similarities = _st_util.cos_sim(jd_embedding, batch_embeddings)[0].tolist()

    # Apply behavioral overlays
    for idx, candidate in enumerate(valid_candidates):
        similarity = similarities[idx]
        skill_score = max(0.0, min(100.0, similarity * 100 * 1.2))
        
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

        score = max(0.0, min(100.0, base_tech_score * multiplier))
        years = profile.get("years_of_experience", "N/A")
        
        c_id = candidate.get("candidate_id") or "Unknown_ID"
        name = profile.get("anonymized_name", "Anonymous Candidate")
        title = profile.get("current_title", "Engineer")
        resp_rate_pct = int((signals.get("recruiter_response_rate", 0) or 0) * 100)
        
        reasoning = (
            f"{name} ({title}) matched core vectors at {round(score, 1)}%. "
            f"Maintains a verified {resp_rate_pct}% interaction rate on-platform."
        )
        
        final_ranked_results.append((score, c_id, reasoning, years))
        
    return final_ranked_results


#4 STREAM ORCHESTRATOR WITH TWO-STAGE HEAP
def get_top_100(uploaded_file, jd_requirements):
    """
    Executes a high-performance two-stage retrieval pipeline.
    Filters 100k streaming rows via swift token matches before running heavy deep learning reranking.
    """
    global _cached_jd_text, _cached_jd_embedding
    
    
    jd_words = set(re.findall(r'\w+', jd_requirements.lower()))
    
    
    RETRIEVAL_LIMIT = 1500
    stage1_heap = []
    
    
    for candidate in stream_candidates(uploaded_file):
        if is_honeypot(candidate):
            continue
            
        #match across user skill names
        skills_list = candidate.get("skills", [])
        matched_count = 0
        for s in skills_list:
            skill_name = str(s.get("name", "")).lower()
            if skill_name in jd_words:
                matched_count += 2  # Boost exact skill term phrase matches
            elif any(word in jd_words for word in skill_name.split()):
                matched_count += 1

    
        candidate_id = candidate.get("candidate_id", "")
        
        if len(stage1_heap) < RETRIEVAL_LIMIT:
            heapq.heappush(stage1_heap, (matched_count, candidate_id, candidate))
        else:
            if matched_count > stage1_heap[0][0]:
                heapq.heappushpop(stage1_heap, (matched_count, candidate_id, candidate))

    
    high_value_pool = [item[2] for item in stage1_heap]
    
    if not high_value_pool:
        return []

    # 2. Encode the Job Description once via AI
    model = _get_semantic_model()
    if _cached_jd_text != jd_requirements or _cached_jd_embedding is None:
        _cached_jd_text = jd_requirements
        _cached_jd_embedding = model.encode(jd_requirements, convert_to_tensor=True)

    #Re-ranking over the 1,500 candidates
    all_scored_candidates = rank_retrieved_pool(high_value_pool, _cached_jd_embedding)
    
    #final Top 100 cleanly sorted
    top_100 = heapq.nlargest(100, all_scored_candidates, key=lambda x: x[0])
    return top_100
