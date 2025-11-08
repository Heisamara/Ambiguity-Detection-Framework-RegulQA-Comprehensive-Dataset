"""
Bootstrap weak labels for RegulQA-Ambig dataset (Phase 1)


Purpose:
  - Load regulqa_ambig_pool_capped.csv
  - Apply heuristic rules to auto-label 'ambig_presence', 'ambig_type', 'reg_clause', 'severity'
  - Save a cleaned and labeled file regulqa_ambig_v1.csv
"""

import re
import pandas as pd
from pathlib import Path


INPUT_FILE = r"/Users/amarachi/Documents/AQA/Dataset_T1/RegulQA-Phase1/data/processed/regulqa_ambig_pool_capped.csv"
OUTPUT_FILE = r"/Users/amarachi/Documents/AQA/Dataset_T1/RegulQA-Phase1/data/processed/regulqa_ambig_v11.csv"


# 2. LOAD DATASET

print("Loading dataset...")

for enc in ("utf-8", "utf-8-sig", "latin1"):
    try:
        df = pd.read_csv(INPUT_FILE, encoding=enc)
        break
    except Exception as e:
        last_err = e

if df is None:
    raise RuntimeError(f"❌ Failed to read {INPUT_FILE}: {last_err}")

print(f"✅ Loaded {df.shape[0]} rows and {df.shape[1]} columns.")

if "req_text" not in df.columns:
    raise ValueError(f"❌ 'req_text' column missing. Found: {list(df.columns)}")


# 3. DEFINE HEURISTICS AND CLAUSE MAPPING

heuristics = {
    "vague_term": (r"\b(as soon as possible|as appropriate|as far as possible|as necessary|if feasible|"
                   r"sufficient|adequate|optimal|user[- ]?friendly|appropriate|relevant|"
                   r"quickly|fast|minimi[sz]e|maximi[sz]e|soon|frequently|periodically|regularly|"
                   r"robust|reliable|secure|safe(ly)?|intuitive|efficient|effective)\b", "lexical"),
    "comparative": (r"\b(better|faster|higher|lower|best|worst|least|most|improv(e|ed|ement))\b", "lexical"),
    "modal_vague": (r"\b(should|may|could|might)\b", "lexical"),
    "passive": (r"\b(shall be|must be|will be|to be)\b", "syntactic"),
    "unbounded": (r"\b(always|never|asap)\b", "lexical"),
    "anaphora": (r"^(it|they|this|that)\b", "semantic"),
}

compiled = {k: (re.compile(pat, re.IGNORECASE), typ) for k, (pat, typ) in heuristics.items()}

clause_map = {
    "vague_term": ["ISO 29148 §5.2.3", "ISO 26262-8 §6.4.3"],
    "comparative": ["ISO 29148 §5.2.4"],
    "modal_vague": ["ISO 29148 §5.2.3"],
    "passive": ["ISO 29148 §5.2 (clarity & testability)"],
    "unbounded": ["ISO 29148 §5.2.4"],
    "anaphora": ["ISO 29148 §5.2.3"],
}


# 4. APPLY HEURISTICS

ambig_presence, ambig_type, reg_clause, severity, notes = [], [], [], [], []

for txt in df["req_text"].astype(str):
    flags, types, matched_clauses, local_notes = [], set(), set(), []

    for name, (pat, typ) in compiled.items():
        if pat.search(txt):
            flags.append(name)
            types.add(typ)
            for c in clause_map.get(name, []):
                matched_clauses.add(c)
            local_notes.append(name)

    # Label assignment
    if flags:
        ambig_presence.append("ambiguous")
        ambig_type.append(";".join(sorted(types)))
        reg_clause.append("; ".join(sorted(matched_clauses)))
    else:
        ambig_presence.append("clear")
        ambig_type.append("")
        reg_clause.append("")

    # Severity logic
    has_high_term = bool(re.search(
        r"\b(brake|emergency|shutdown|stop|hazard|fault|safety|alarm|ventilator|infusion|dose|radiation|landing|autopilot|airbag)\b",
        txt, re.IGNORECASE
    ))

    if flags:
        if any(f in ("vague_term", "unbounded", "modal_vague") for f in flags) and has_high_term:
            sev = "high"
        elif "passive" in flags and not has_high_term:
            sev = "low"
        else:
            sev = "medium"
    else:
        sev = ""
    severity.append(sev)
    notes.append(", ".join(local_notes))

# Attach columns (don’t overwrite if filled)
def prefer_new(old_series, new_list):
    if old_series is None:
        return new_list
    out = []
    for old, new in zip(old_series, new_list):
        if pd.isna(old) or str(old).strip() == "":
            out.append(new)
        else:
            out.append(old)
    return out

for col, new_vals in {
    "ambig_presence": ambig_presence,
    "ambig_type": ambig_type,
    "reg_clause": reg_clause,
    "severity": severity,
    "notes": notes
}.items():
    df[col] = prefer_new(df[col] if col in df.columns else [None]*len(new_vals), new_vals)


# 5. QUALITY SUMMARY
print("\n=== QUALITY SUMMARY ===")
print("Total rows:", len(df))
print("\nambig_presence distribution:\n", df["ambig_presence"].value_counts())
print("\nTop ambig_type (ambiguous only):\n",
      df.loc[df["ambig_presence"] == "ambiguous", "ambig_type"].value_counts().head(10))
print("\nDuplicate req_text entries:", df.duplicated(subset=["req_text"]).sum())


# 6. SAVE FINAL LABELED DATA

Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print(f"\n✅ Labeled dataset written to:\n{OUTPUT_FILE}")
print("You can now proceed to Phase 2: Pre-processing & Feature Extraction.")