"""
Normalize & unify T1/T2/T3 into an annotation-ready pool with sector inference.
"""
from pathlib import Path
import pandas as pd, re, yaml

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
INTERIM.mkdir(parents=True, exist_ok=True); PROCESSED.mkdir(parents=True, exist_ok=True)

SECTOR_HINTS = {
    "automotive": ["automotive","vehicle","car","iso 26262","ecu","autonomous"],
    "medical": ["medical","health","patient","device","iec 62304","hl7","fhir"],
    "aerospace": ["aerospace","space","nasa","avionics","do-178c","aircraft"],
    "rail": ["rail","train","signaling","ertms"],
    "finance": ["bank","finance","trading","payment","pci"],
    "defense": ["defense","military","weapon"],
    "energy": ["grid","energy","power plant","scada"],
}

def _normalize_text(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s

def _infer_sector(row, overrides):
    # 1) overrides by document
    doc = str(row.get("document","")).strip()
    if overrides and doc in overrides:
        return str(overrides[doc]).strip()
    # 2) rule-based
    if row.get("source") == "NASA_TRICK_SRS":
        return "aerospace"
    s = (str(row.get("document","")) + " " + str(row.get("req_text",""))).lower()
    for sector, keys in SECTOR_HINTS.items():
        if any(k in s for k in keys):
            return sector
    return "general"

def _read_any_csv(path):
    try:
        return pd.read_csv(path)
    except Exception:
        try:
            return pd.read_csv(path, sep=None, engine="python")
        except Exception:
            return None

def build_pool():
    frames = []
    # Load sector overrides if provided
    ov_path = ROOT / "config" / "sector_overrides.yaml"
    overrides = yaml.safe_load(ov_path.read_text()) if ov_path.exists() else {}

    # T1: PURE, PROMISE, NASA Trick
    for folder, source in [("t1_pure","PURE"),("t1_promise_exp","PROMISE_EXP"),("t1_nasa_srs","NASA_TRICK_SRS"),
                           ("t2_synthetic","SYNTHETIC"),("t3_domain","DOMAIN") ]:
        for f in (RAW/folder).rglob("*.csv"):
            df = _read_any_csv(f)
            if df is None or df.empty: continue
            # find text column
            textcol = next((c for c in df.columns if c.lower() in {"text","sentence","req_text","requirement","requirements"}), None)
            if textcol is None and "req_text" in df.columns: textcol = "req_text"
            if not textcol: continue
            tmp = pd.DataFrame({
                "source": source,
                "tier": "T1" if folder.startswith("t1_") else ("T2" if folder.startswith("t2_") else "T3"),
                "document": f.name,
                "req_text": df[textcol].astype(str).map(_normalize_text)
            })
            frames.append(tmp)

    if not frames:
        print("No raw files found. Download or add T2/T3 first.")
        return None

    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df[all_df["req_text"].str.len()>5].drop_duplicates(subset=["req_text"]).reset_index(drop=True)

    # ids
    def make_id(i,row):
        prefix = {"PURE":"PURE","PROMISE_EXP":"PROM","NASA_TRICK_SRS":"NASA","SYNTHETIC":"SYN","DOMAIN":"DOM"}.get(row["source"],"UNK")
        return f"{prefix}_{i:06d}"
    all_df["id"] = [make_id(i,r) for i,r in enumerate(all_df.to_dict("records"))]

    # sector
    all_df["sector"] = [ _infer_sector(r, overrides) for r in all_df.to_dict("records") ]

    # empty annotation cols
    for c in ["ambig_presence","ambig_type","reg_clause","severity","notes"]:
        all_df[c] = ""

    cols = ["id","source","tier","sector","document","req_text","ambig_presence","ambig_type","reg_clause","severity","notes"]
    all_df = all_df[cols]
    out = PROCESSED / "regulqa_ambig_pool.csv"
    all_df.to_csv(out, index=False)
    print("Wrote", out, "rows:", len(all_df))
    return all_df

if __name__ == "__main__":
    build_pool()
