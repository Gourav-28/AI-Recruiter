import argparse
import pandas as pd
from engine import get_top_100

def main():
    parser = argparse.ArgumentParser(description="Redrob Hackathon Core Ranking Pipeline")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Path to save output team_xxx.csv")
    args = parser.parse_args()

    print("Running pipeline execution bridge...")
    
    # Open the file in binary mode ('rb') to match Streamlit's binary stream output
    with open(args.candidates, 'rb') as f:
        raw_results = get_top_100(
            f, 
            "Looking for Core Software Engineers, NLP systems expert, Rust/Python production exp."
        )
    
    if not raw_results:
        print("Error: No results generated from ranking engine.")
        return

    # Format precisely to submission specification
    formatted_data = []
    for idx, item in enumerate(raw_results, 1):
        # Unpack based on your engine's returned tuple/list structure
        score, c_id, reasoning = item[0], item[1], item[2]
        
        formatted_data.append({
            "candidate_id": str(c_id),
            "rank": int(idx),
            "score": float(score),
            "reasoning": str(reasoning)
        })
        
    df = pd.DataFrame(formatted_data)
    
    # Format Validation Checks before exporting
    assert len(df) == 100, f"Row count must be exactly 100. Found: {len(df)}"
    
    # Save the output file
    df.to_csv(args.out, index=False, encoding='utf-8')
    print(f"Submission successfully generated and verified at: {args.out}")

if __name__ == "__main__":
    main()