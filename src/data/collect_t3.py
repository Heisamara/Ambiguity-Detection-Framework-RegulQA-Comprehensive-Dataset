"""
Helper to aggregate your manually collected T3 (public SRS/manuals) into CSV.
Usage:
- Drop any CSVs with a 'req_text' column into data/raw/t3_domain
- Or run this to combine small text lists into a single CSV
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
T3 = ROOT / "data" / "raw" / "t3_domain"
OUT = T3 / "domain_collected.csv"

def collect():
    frames = []
    for f in T3.rglob("*.csv"):
        try:
            df = pd.read_csv(f)
            if "req_text" in df.columns:
                frames.append(df[["req_text"]].assign(document=f.name))
        except Exception:
            pass
    if frames:
        all_df = pd.concat(frames, ignore_index=True)
        all_df.to_csv(OUT, index=False)
        print("Collected →", OUT, "rows:", len(all_df))
    else:
        print("No CSVs with 'req_text' found in", T3)

if __name__ == "__main__":
    collect()
