from pathlib import Path
import pandas as pd, random

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'data'/'raw'/'t2_synthetic'; OUT.mkdir(parents=True, exist_ok=True)

AUTOMOTIVE_TPL = [
    "Per ISO 26262, the ECU shall {verb} the braking command within {ms} ms under {cond}.",
    "The vehicle control unit shall {verb} torque request when {cond} in accordance with ISO 26262.",
    "The autonomous driving stack shall {verb} sensor fusion output within {ms} ms (ISO 26262 ASIL).",
]
MEDICAL_TPL = [
    "As required by IEC 62304, the medical device software shall {verb} patient vitals at an interval of {ms} ms.",
    "The device shall {verb} alarm when {cond} per IEC 62304 risk control requirements.",
    "Per IEC 62304, the software shall {verb} dosage calculation when {cond}.",
]
AERO_TPL = [
    "In accordance with DO-178C avionics objectives, the flight SW shall {verb} telemetry packets within {ms} ms after {cond}.",
    "DO-178C: The system shall {verb} mode transition when {cond}.",
    "Per DO-178C, the avionics application shall {verb} command dispatch within {ms} ms.",
]

VERBS = ["log","validate","transmit","compute","limit","store"]
MSEC = ["10","20","50","100","200"]
CONDS = ["loss of signal","over-temperature","sensor fault","voltage drop"]

def gen_block(templates, sector, n=100):
    rows = []
    for i in range(n):
        t = random.choice(templates)
        s = t.format(verb=random.choice(VERBS), ms=random.choice(MSEC), cond=random.choice(CONDS))
        rows.append({"sector": sector, "document": f"{sector.upper()}_SYNTH", "req_text": s})
    return pd.DataFrame(rows)

def make_synthetic(n_each=100):
    df = pd.concat([
        gen_block(AUTOMOTIVE_TPL,"automotive", n_each),
        gen_block(MEDICAL_TPL,"medical", n_each),
        gen_block(AERO_TPL,"aerospace", n_each),
    ], ignore_index=True)
    out = OUT/"synthetic_requirements.csv"
    df.to_csv(out, index=False); print("Synthetic →", out, "rows:", len(df))

if __name__ == "__main__":
    make_synthetic()
